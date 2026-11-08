import asyncio
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

os.environ.setdefault('DATABASE_URL', 'postgresql+asyncpg://test:test@localhost/test')
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from starlette.datastructures import UploadFile
from backend.api.files_router import router
from backend.services import ingestion, file_storage
from backend.services.csv_parser import enrich_csv


class IngestionTests(unittest.IsolatedAsyncioTestCase):
    async def test_cleanup_and_pending_after_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'enriched.csv'
            path.touch()
            committed = AsyncMock()
            async def fail_index(_):
                self.assertFalse(path.exists())
                committed.assert_awaited_once()
                raise RuntimeError('index offline')
            with patch.object(ingestion, 'enrich_csv', return_value=str(path)), patch.object(
                ingestion, 'process_csv_to_pg_db', committed
            ), patch.object(ingestion, 'index_file', fail_index):
                result = await ingestion.process_csv_to_db('source.csv', 'Category', 'Subject')
            self.assertEqual(result['status'], 'indexing_pending')
            self.assertTrue(result['retryable'])

    async def test_cleanup_on_database_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'enriched.csv'
            path.touch()
            with patch.object(ingestion, 'enrich_csv', return_value=str(path)), patch.object(
                ingestion, 'process_csv_to_pg_db', AsyncMock(side_effect=RuntimeError('db offline'))
            ), patch.object(ingestion, 'index_file', AsyncMock()) as index:
                with self.assertRaises(RuntimeError):
                    await ingestion.process_csv_to_db('source.csv', 'Category', 'Subject')
                index.assert_not_awaited()
            self.assertFalse(path.exists())

    async def test_same_filename_unique_storage(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(file_storage, 'UPLOAD_ROOT', Path(directory)):
            first = await file_storage.save_upload_file(UploadFile(io.BytesIO(b'one'), filename='terms.csv'))
            second = await file_storage.save_upload_file(UploadFile(io.BytesIO(b'two'), filename='terms.csv'))
            self.assertNotEqual(first, second)
            self.assertEqual(Path(first).name, 'terms.csv')
            self.assertEqual(Path(first).read_bytes(), b'one')
            self.assertEqual(Path(second).read_bytes(), b'two')


class ApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        app = FastAPI()
        app.include_router(router)
        self.client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_validation_error_and_cleanup(self):
        with patch('backend.api.files_router.save_upload_file', AsyncMock(return_value='saved.csv')), patch(
            'backend.api.files_router.open', unittest.mock.mock_open()
        ), patch('backend.api.files_router.validate_file_type', side_effect=ValueError('bad CSV')), patch(
            'backend.api.files_router.remove_upload'
        ) as cleanup:
            response = await self.client.post('/file/upload', files={'file': ('terms.csv', b'invalid')}, data={'category': 'c', 'subject': 's'})
        self.assertEqual(response.status_code, 422)
        cleanup.assert_called_once_with('saved.csv')

    async def test_server_failure_is_not_success(self):
        with patch('backend.api.files_router.save_upload_file', AsyncMock(side_effect=OSError('disk full'))):
            response = await self.client.post('/file/upload', files={'file': ('terms.csv', b'term,definition\na,b')}, data={'category': 'c', 'subject': 's'})
        self.assertEqual(response.status_code, 500)

    async def test_retry_missing_and_success(self):
        with patch('backend.services.ingestion.index_file', AsyncMock(side_effect=LookupError())):
            self.assertEqual((await self.client.post('/file/retry-index', json={'path': 'missing'})).status_code, 404)
        with patch('backend.services.ingestion.index_file', AsyncMock()):
            response = await self.client.post('/file/retry-index', json={'path': 'saved.csv'})
        self.assertEqual(response.json()['status'], 'indexed')


class ChromaTests(unittest.TestCase):
    def test_persistent_upsert_query_delete(self):
        from backend.chroma import connection, term_repository
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'CHROMA_PATH': directory, 'CHROMA_COLLECTION': 'test_terms'}):
            connection.get_client.cache_clear()
            connection.get_collection.cache_clear()
            try:
                term_repository.upsert_vectors(['a'], [[1., 0., 0.]], [{'term': 'first'}])
                term_repository.upsert_vectors(['a'], [[0., 1., 0.]], [{'term': 'updated'}])
                import chromadb
                reopened_client = chromadb.PersistentClient(path=directory)
                reopened = reopened_client.get_collection('test_terms')
                self.assertEqual(reopened.count(), 1)
                self.assertEqual(reopened.get(ids=['a'])['metadatas'][0]['term'], 'updated')
                reopened_client.close()
                self.assertEqual(term_repository.query_vectors([0., 1., 0.]), ['a'])
                term_repository.delete_vector('a')
                self.assertEqual(term_repository.query_vectors([0., 1., 0.]), [])
            finally:
                connection.get_client().close()
                connection.get_collection.cache_clear()
                connection.get_client.cache_clear()


if __name__ == '__main__':
    unittest.main()
