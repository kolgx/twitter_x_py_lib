import asyncio
import httpx
from typing import Optional
from .network_utils import quote_url

class AsyncDownloader:
    def __init__(self, max_concurrent: int, proxy: Optional[str] = None, log_output: bool = False):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.proxy = proxy
        self.log_output = log_output
        self.tasks = []
        self.success_count = 0
        self.fail_count = 0
        return

    def add_task(self, url: str, file_path: str):
        if not url or url == '':
            return
        if not file_path or file_path == '':
            return

        self.tasks.append({
            'url': url,
            'file_path': file_path
        })
        return

    async def _download_file(self, task: dict):
        url = task['url']
        file_path = task['file_path']

        if '.mp4' not in url:
            url += '?name=orig'

        count = 0
        while True:
            try:
                async with self.semaphore:
                    async with httpx.AsyncClient(proxy=self.proxy) as client:
                        response = await client.get(quote_url(url), timeout=(3.05, 16))
                        if response.status_code == 404:
                            raise Exception('404')
                            
                with open(file_path, 'wb') as f:
                    f.write(response.content)

                if self.log_output:
                    print(f'{file_path}=====>下载完成')
                    
                self.success_count += 1
                break
                
            except Exception as e:
                count += 1
                if count >= 50:
                    if self.log_output:
                        print(f'{file_path}=====>第{count}次下载失败{e}，已跳过该文件。')
                        print(url)
                    self.fail_count += 1
                    break

                if self.log_output:
                    print(f'{file_path}=====>第{count}次下载失败{e},正在重试')
                    print(url)
        return

    async def _run_all(self):
        coros = [self._download_file(t) for t in self.tasks]
        await asyncio.gather(*coros)
        self.tasks.clear()
        return

    def start(self):
        if not self.tasks:
            return
        asyncio.run(self._run_all())
        return

    def get_status(self):
        return {
            'success_count': self.success_count,
            'fail_count': self.fail_count,
            'pending_tasks': len(self.tasks)
        }
