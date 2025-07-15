import multiprocessing
import threading
from multiprocessing.managers import SyncManager

from bs4 import BeautifulSoup

from config import logger, settings
from scraper.request import Request


class IBKR:

    THREAD_COUNT = settings.THREAD_COUNT

    def __init__(self, tickers):
        logger.info("Initializing IBKR instance")
        self.request = Request().request
        self.tickers = tickers
        self.result = {}
        self.tasks = []

    def run(self):
        logger.info("IBKR run started")
        self.tasks = self.tickers.copy()
        logger.info("Fetched %d Tickers", len(self.tickers))
        self.start_workers()
        logger.info("All processes and threads have completed")
        return dict(self.result)

    def start_workers(self):
        manager = self._start_sync_manager()
        self.tasks = manager.list(self.tasks)
        self.result = manager.dict()
        lock = manager.RLock()
        n_proc = multiprocessing.cpu_count()
        logger.info(
            "Starting %d processes × %d threads each", n_proc, self.THREAD_COUNT
        )
        processes = [
            multiprocessing.Process(
                target=self._process_target,
                name=f"Proc-{i}",
                args=(lock,),
            )
            for i in range(n_proc)
        ]

        for p in processes:
            p.start()
            logger.debug("Started %s", p.name)

        for p in processes:
            p.join()
            logger.debug("%s has finished", p.name)

    def _process_target(self, lock):
        local_threads = [
            threading.Thread(
                target=self.worker,
                name=f"{multiprocessing.current_process().name}-T{t}",
                args=(lock,),
                daemon=True,
            )
            for t in range(self.THREAD_COUNT)
        ]

        for t in local_threads:
            t.start()

        for t in local_threads:
            t.join()

    def worker(self, lock):
        thread_name = threading.current_thread().name
        logger.debug("%s: started", thread_name)

        while True:
            with lock:
                if not self.tasks:
                    logger.debug("%s: no more tasks", thread_name)
                    break
                ticker_data = self.tasks.pop(0)

            ticker = f'{ticker_data["symbol"]}.{ticker_data["exch"]}'
            url = ticker_data["url"]
            if ticker in self.result:
                logger.debug("%s: skipping duplicate ticker %s", thread_name, ticker)
                continue

            try:
                logger.debug("%s: fetching ESG scores for %s", thread_name, ticker)
                data = self.fetch_contract(url)
                with lock:
                    self.result[ticker] = {**ticker_data, **data}
                logger.debug("%s: fetched data for %s", thread_name, ticker)
            except Exception as e:
                logger.warning(
                    "%s: unable to fetch data for %s: %s", thread_name, ticker, e
                )

    def fetch_contract(self, url):
        logger.debug("Fetching contract from %s", url)
        resp = self.request("GET", url)
        resp.raise_for_status()
        result = self._fetch_contract(resp.text)
        return result

    def _fetch_contract(self, html):
        result = {}
        fields = [
            "ASSETID",
            "ISIN",
            "CONID",
            "Closing Price",
            "Contract Type",
            "Exchange",
            "Country/Region",
        ]

        soup = BeautifulSoup(html, "html.parser")
        trs = soup.find_all("tr")
        for tr in trs:
            field = tr.find("th")
            value = tr.find("td")
            if not field:
                continue
            if "Website" in field.text:
                continue
            if not value:
                continue

            for f in fields:
                if f not in field.text:
                    continue

                result[f] = value.text.strip()
                if f == "Exchange":
                    result["Primary Exchange"] = value.text.strip().split(", ")[0]

        return result

    @staticmethod
    def _start_sync_manager():
        m = SyncManager(address=("127.0.0.1", 0), authkey=b"ibkr")
        m.start()
        return m
