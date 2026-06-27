from __future__ import annotations

import argparse
import asyncio
import logging
from dataclasses import dataclass
from tqdm import tqdm
from vk_checker.artifacts import save_error_artifacts
from vk_checker.browser import BrowserManager
from vk_checker.cache import ResultCache
from vk_checker.checkpoint import CheckpointManager
from vk_checker.config import Settings
from vk_checker.exporter import Exporter
from vk_checker.google_sheet import GoogleSheetClient
from vk_checker.logger import setup_logging
from vk_checker.models import CandidateClass, ExportRecord, ProcessingStats, SheetRow
from vk_checker.rate_limit import AsyncRateLimiter, LimitConfig
from vk_checker.rules import HeuristicRules, HeuristicScorer
from vk_checker.scraper import VKScraper
from vk_checker.stats import StatsReporter, print_stats
from vk_checker.validation import analyze_validation_xlsx, records_to_validation_xlsx, sample_rows, validation_has_verdicts
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CliArgs:
    resume: bool
    retry_errors: bool
    dry_run: bool
    export_candidates: bool
    stats: bool
    workers: int | None
    start_row: int | None
    end_row: int | None
    config: str
    rules: str
    command: str | None
    validation_count: int
    validation_file: str
    quality_report: str


def parse_args() -> CliArgs:
    parser = argparse.ArgumentParser(description="VK community data collector and heuristic candidate filter")
    parser.add_argument("command", nargs="?", choices=["validate_rules"], help="run rule quality validation workflow")
    parser.add_argument("--resume", action="store_true", help="continue from rows without completed check")
    parser.add_argument("--retry-errors", action="store_true", help="process only rows marked as error")
    parser.add_argument("--dry-run", action="store_true", help="scrape VK and write JSON files only; no Google writes")
    parser.add_argument("--export-candidates", action="store_true", help="export only A/B candidates for BotHelp AI")
    parser.add_argument("--stats", action="store_true", help="print aggregate run statistics")
    parser.add_argument("--workers", type=int, help="override MAX_CONCURRENT")
    parser.add_argument("--range", dest="row_range", help="Google Sheet row range, e.g. 1000-2000")
    parser.add_argument("--config", default="config.yaml", help="YAML project config path")
    parser.add_argument("--rules", help="YAML heuristic rules path")
    parser.add_argument("--validation-count", type=int, default=100, help="number of random communities for validate_rules")
    parser.add_argument("--validation-file", default="exports/validation.xlsx", help="validation workbook path")
    parser.add_argument("--quality-report", default="exports/quality_report.html", help="quality report HTML path")
    ns = parser.parse_args()
    start_row = end_row = None
    if ns.row_range:
        left, right = ns.row_range.replace("–", "-").split("-", 1)
        start_row, end_row = int(left), int(right)
        if start_row > end_row:
            raise SystemExit("--range start must be <= end")
    return CliArgs(ns.resume, ns.retry_errors, ns.dry_run, ns.export_candidates, ns.stats, ns.workers, start_row, end_row, ns.config, ns.rules, ns.command, ns.validation_count, ns.validation_file, ns.quality_report)


async def process_row(
    row: SheetRow,
    browser: BrowserManager,
    scraper: VKScraper,
    sheet: GoogleSheetClient,
    cache: ResultCache,
    settings: Settings,
    scorer: HeuristicScorer,
    stats: ProcessingStats,
    reporter: StatsReporter,
    progress: tqdm,
    stats_lock: asyncio.Lock,
    checkpoint: CheckpointManager,
    exporter: Exporter,
    records: list[ExportRecord],
    dry_run: bool,
) -> None:
    page = await browser.new_page()
    record = ExportRecord(row_number=row.row_number, url=row.url, status="pending")
    try:
        data = await scraper.scrape(page, row.url)
        record.scraped = data
        content_hash = cache.content_hash(data)
        heuristic = cache.get(row.url, content_hash)
        if heuristic is None:
            heuristic = scorer.evaluate(data)
            cache.set(row.url, content_hash, heuristic)
        record.heuristic = heuristic
        if dry_run:
            record.status = "dry_run"
            exporter.export_dry_run(record)
        else:
            record.status = "done"
            await asyncio.to_thread(sheet.write_result, row.row_number, heuristic)
        async with stats_lock:
            stats.processed += 1
            stats.total_score += heuristic.score
            stats.last_row = max(stats.last_row, row.row_number)
            if heuristic.candidate_class == CandidateClass.HIGH:
                stats.high_probability += 1
            elif heuristic.candidate_class == CandidateClass.MEDIUM:
                stats.medium_probability += 1
            else:
                stats.low_probability += 1
            records.append(record)
            checkpoint.maybe_save(stats.processed, stats.last_row, stats, cache.count())
            reporter.maybe_report()
            progress.update(1)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logger.exception("Failed to process row %s url %s", row.row_number, row.url)
        try:
            html_path, png_path = await save_error_artifacts(page, settings.project.artifacts_dir, row.row_number, row.url)
            message = f"{type(exc).__name__}: {exc}; artifacts: {html_path}, {png_path}"
        except Exception as artifact_exc:
            logger.exception("Failed to save error artifacts for row %s", row.row_number)
            message = f"{type(exc).__name__}: {exc}; artifact_error: {artifact_exc}"
        if not dry_run:
            await asyncio.to_thread(sheet.write_error, row.row_number, message)
        record.status = "error"
        record.error = message
        async with stats_lock:
            stats.processed += 1
            stats.errors += 1
            stats.last_row = max(stats.last_row, row.row_number)
            records.append(record)
            checkpoint.maybe_save(stats.processed, stats.last_row, stats, cache.count())
            reporter.maybe_report()
            progress.update(1)
    finally:
        if not page.is_closed():
            await page.close()


async def worker(name: str, queue: asyncio.Queue[SheetRow], *args: object) -> None:
    while True:
        row = await queue.get()
        try:
            await process_row(row, *args)  # type: ignore[arg-type]
        finally:
            queue.task_done()


async def run() -> None:
    cli = parse_args()
    settings = Settings.load(cli.config)
    if cli.workers:
        object.__setattr__(settings, "max_concurrent", max(1, cli.workers))
    setup_logging(settings.log_level)
    checkpoint = CheckpointManager(settings.project.checkpoint_path, settings.project.checkpoint_interval)
    checkpoint_row = checkpoint.load().last_row if cli.resume and not cli.retry_errors else 0
    sheet = GoogleSheetClient(settings.google_sheet_id, settings.google_service_account, settings.input_sheet_name, settings.input_column, settings.start_row, settings.rate_limits.google_sheets_rpm, settings.rate_limits.jitter_ms)
    if cli.command == "validate_rules" and Path(cli.validation_file).exists() and await asyncio.to_thread(validation_has_verdicts, cli.validation_file):
        metrics = await asyncio.to_thread(analyze_validation_xlsx, cli.validation_file, cli.quality_report)
        logger.info("Validation metrics: precision=%.3f recall=%.3f f1=%.3f accuracy=%.3f", metrics.precision, metrics.recall, metrics.f1, metrics.accuracy)
        return
    if cli.dry_run or cli.command == "validate_rules":
        rows = await asyncio.to_thread(sheet.input_rows, cli.start_row, cli.end_row, checkpoint_row)
    else:
        await asyncio.to_thread(sheet.ensure_headers)
        rows = await asyncio.to_thread(sheet.rows, cli.start_row, cli.end_row, cli.retry_errors, True if cli.resume or not cli.retry_errors else False, checkpoint_row)
    if cli.command == "validate_rules":
        rows = sample_rows(rows, cli.validation_count)
    stats = ProcessingStats()
    reporter = StatsReporter(len(rows), settings.project.progress_interval, stats, settings.monitoring.error_spike_threshold)
    cache = ResultCache(settings.project.cache_path)
    exporter = Exporter(settings.project.export_dir)
    scorer = HeuristicScorer(HeuristicRules.load(cli.rules or settings.prefilter.rules_path))
    playwright_limiter = AsyncRateLimiter(LimitConfig(settings.rate_limits.playwright_rpm, settings.rate_limits.jitter_ms))
    scraper = VKScraper(settings.scraping, playwright_limiter)
    stats_lock = asyncio.Lock()
    records: list[ExportRecord] = []
    queue: asyncio.Queue[SheetRow] = asyncio.Queue(maxsize=settings.max_concurrent * 4)
    async with BrowserManager(settings.profile_dir, settings.headless) as browser:
        with tqdm(total=len(rows), desc="VK checks", unit="community") as progress:
            workers = [asyncio.create_task(worker(f"worker-{i}", queue, browser, scraper, sheet, cache, settings, scorer, stats, reporter, progress, stats_lock, checkpoint, exporter, records, cli.dry_run or cli.command == "validate_rules")) for i in range(settings.max_concurrent)]
            try:
                for row in rows:
                    await queue.put(row)
                await queue.join()
            except KeyboardInterrupt:
                logger.warning("Interrupted by user. Checkpoint and already written rows are preserved; rerun with --resume.")
            finally:
                for task in workers:
                    task.cancel()
                await asyncio.gather(*workers, return_exceptions=True)
    checkpoint.save(stats.last_row, stats, cache.count())
    reporter.report()
    exporter.export(records, stats)
    if cli.command == "validate_rules":
        records_to_validation_xlsx(records, cli.validation_file)
        logger.info("Validation workbook written to %s. Fill Human verdict and run validate_rules again.", cli.validation_file)
    if cli.export_candidates:
        logger.info("Candidate export written to %s", exporter.export_candidates(records))
    if cli.stats:
        print(print_stats(records, scorer.positive_counter, scorer.negative_counter))


def main() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.warning("Stopped by Ctrl+C")


if __name__ == "__main__":
    main()
