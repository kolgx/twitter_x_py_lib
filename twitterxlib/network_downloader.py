import httpx
import threading
from typing import Optional
from pathlib import Path
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor
from .simple_tool_utils import quote_url


class AsyncDownloader:
    def __init__(self, max_concurrent: int, proxy: Optional[str] = None, log_output: bool = False):
        self.max_concurrent = max_concurrent
        self.proxy = proxy
        self.log_output = log_output
        self.tasks = []
        self.success_count = 0
        self.fail_count = 0
        self._lock = threading.Lock()
        return

    def add_task(self, url: str, file_path: str):
        if not url:
            return
        if not file_path:
            return
        self.tasks.append({'url': url, 'file_path': file_path})

    def _download_one(self, task: dict, client: httpx.Client):
        url = task['url']
        file_path = task['file_path']

        if '.mp4' not in url:
            url += '?name=orig'

        count = 0
        while True:
            try:
                response = client.get(quote_url(url), timeout=(3.05, 16))
                if response.status_code == 404:
                    raise Exception('404')

                path = Path(file_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, 'wb') as f:
                    f.write(response.content)

                if self.log_output:
                    print(f'{file_path}=====>下载完成')

                with self._lock:
                    self.success_count += 1
                return

            except Exception as e:
                count += 1
                if count >= 50:
                    if self.log_output:
                        print(f'{file_path}=====>第{count}次下载失败{e}，已跳过该文件。')
                        print(url)
                    with self._lock:
                        self.fail_count += 1
                    return

                if self.log_output:
                    print(f'{file_path}=====>第{count}次下载失败{e},正在重试')
                    print(url)

    def _worker(self, task_queue: Queue, client: httpx.Client):
        while True:
            try:
                task = task_queue.get(timeout=0.5)
            except Empty:
                return
            if task is None:
                return
            try:
                self._download_one(task, client)
            except Exception as e:
                if self.log_output:
                    print(f'failed to download {task.get("url")} to {task.get("file_path")}, error: {e}')
            finally:
                task_queue.task_done()

    def start(self):
        if not self.tasks:
            return

        task_queue = Queue()
        for t in self.tasks:
            task_queue.put(t)

        client = httpx.Client(proxy=self.proxy)
        try:
            worker_count = min(self.max_concurrent, len(self.tasks))
            with ThreadPoolExecutor(max_workers=worker_count) as executor:
                for _ in range(worker_count):
                    executor.submit(self._worker, task_queue, client)
        finally:
            client.close()

        self.tasks.clear()
        return

    def get_status(self):
        return {
            'success_count': self.success_count,
            'fail_count': self.fail_count,
            'pending_tasks': len(self.tasks)
        }