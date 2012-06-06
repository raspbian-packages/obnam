# Copyright (C) 2010-2011  Lars Wirzenius
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import hashlib
import os
import shutil
import stat
import tempfile
import time
import unittest

import obnamlib


class RepositoryRootNodeTests(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

        self.fs = obnamlib.LocalFS(self.tempdir)
        self.repo = obnamlib.Repository(self.fs, obnamlib.DEFAULT_NODE_SIZE,
                                        obnamlib.DEFAULT_UPLOAD_QUEUE_SIZE,
                                        obnamlib.DEFAULT_LRU_SIZE, None,
                                        obnamlib.IDPATH_DEPTH,
                                        obnamlib.IDPATH_BITS,
                                        obnamlib.IDPATH_SKIP,
                                        time.time, 0, '')
        
        self.otherfs = obnamlib.LocalFS(self.tempdir)
        self.other = obnamlib.Repository(self.fs, obnamlib.DEFAULT_NODE_SIZE,
                                         obnamlib.DEFAULT_UPLOAD_QUEUE_SIZE,
                                         obnamlib.DEFAULT_LRU_SIZE, None,
                                        obnamlib.IDPATH_DEPTH,
                                        obnamlib.IDPATH_BITS,
                                        obnamlib.IDPATH_SKIP,
                                        time.time, 0, '')

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_has_format_version(self):
        self.assert_(hasattr(self.repo, 'format_version'))

    def test_accepts_same_format_version(self):
        self.assert_(self.repo.acceptable_version(self.repo.format_version))

    def test_does_not_accept_older_format_version(self):
        older_version = self.repo.format_version - 1
        self.assertFalse(self.repo.acceptable_version(older_version))

    def test_does_not_accept_newer_version(self):
        newer_version = self.repo.format_version + 1
        self.assertFalse(self.repo.acceptable_version(newer_version))
        
    def test_has_none_version_for_empty_repository(self):
        self.assertEqual(self.repo.get_format_version(), None)
        
    def test_creates_repository_with_format_version(self):
        self.repo.lock_root()
        self.assertEqual(self.repo.get_format_version(), 
                         self.repo.format_version)

    def test_lists_no_clients(self):
        self.assertEqual(self.repo.list_clients(), [])

    def test_has_not_got_root_node_lock(self):
        self.assertFalse(self.repo.got_root_lock)

    def test_locks_root_node(self):
        self.repo.lock_root()
        self.assert_(self.repo.got_root_lock)
        
    def test_locking_root_node_twice_fails(self):
        self.repo.lock_root()
        self.assertRaises(obnamlib.Error, self.repo.lock_root)
        
    def test_commit_releases_lock(self):
        self.repo.lock_root()
        self.repo.commit_root()
        self.assertFalse(self.repo.got_root_lock)
        
    def test_unlock_releases_lock(self):
        self.repo.lock_root()
        self.repo.unlock_root()
        self.assertFalse(self.repo.got_root_lock)
        
    def test_commit_without_lock_fails(self):
        self.assertRaises(obnamlib.LockFail, self.repo.commit_root)
        
    def test_unlock_root_without_lock_fails(self):
        self.assertRaises(obnamlib.LockFail, self.repo.unlock_root)

    def test_commit_when_locked_by_other_fails(self):
        self.other.lock_root()
        self.assertRaises(obnamlib.LockFail, self.repo.commit_root)

    def test_unlock_root_when_locked_by_other_fails(self):
        self.other.lock_root()
        self.assertRaises(obnamlib.LockFail, self.repo.unlock_root)

    def test_on_disk_repository_has_no_version_initially(self):
        self.assertEqual(self.repo.get_format_version(), None)

    def test_lock_root_adds_version(self):
        self.repo.lock_root()
        self.assertEqual(self.repo.get_format_version(),
                         self.repo.format_version)

    def test_lock_root_fails_if_format_is_incompatible(self):
        self.repo._write_format_version(0)
        self.assertRaises(obnamlib.BadFormat, self.repo.lock_root)

    def test_list_clients_fails_if_format_is_incompatible(self):
        self.repo._write_format_version(0)
        self.assertRaises(obnamlib.BadFormat, self.repo.list_clients)

    def test_locks_shared(self):
        self.repo.lock_shared()
        self.assertTrue(self.repo.got_shared_lock)
        
    def test_locking_shared_twice_fails(self):
        self.repo.lock_shared()
        self.assertRaises(obnamlib.Error, self.repo.lock_shared)

    def test_unlocks_shared(self):
        self.repo.lock_shared()
        self.repo.unlock_shared()
        self.assertFalse(self.repo.got_shared_lock)

    def test_unlock_shared_when_locked_by_other_fails(self):
        self.other.lock_shared()
        self.assertRaises(obnamlib.LockFail, self.repo.unlock_shared)

    def test_lock_client_fails_if_format_is_incompatible(self):
        self.repo._write_format_version(0)
        self.assertRaises(obnamlib.BadFormat, self.repo.lock_client, 'foo')

    def test_open_client_fails_if_format_is_incompatible(self):
        self.repo._write_format_version(0)
        self.assertRaises(obnamlib.BadFormat, self.repo.open_client, 'foo')
        
    def test_adding_client_without_root_lock_fails(self):
        self.assertRaises(obnamlib.LockFail, self.repo.add_client, 'foo')
        
    def test_adds_client(self):
        self.repo.lock_root()
        self.repo.add_client('foo')
        self.assertEqual(self.repo.list_clients(), ['foo'])
        
    def test_adds_two_clients_across_commits(self):
        self.repo.lock_root()
        self.repo.add_client('foo')
        self.repo.commit_root()
        self.repo.lock_root()
        self.repo.add_client('bar')
        self.repo.commit_root()
        self.assertEqual(sorted(self.repo.list_clients()), ['bar', 'foo'])
        
    def test_adds_client_that_persists_after_commit(self):
        self.repo.lock_root()
        self.repo.add_client('foo')
        self.repo.commit_root()
        s2 = obnamlib.Repository(self.fs, obnamlib.DEFAULT_NODE_SIZE,
                                 obnamlib.DEFAULT_UPLOAD_QUEUE_SIZE,
                                 obnamlib.DEFAULT_LRU_SIZE, None,
                                 obnamlib.IDPATH_DEPTH,
                                 obnamlib.IDPATH_BITS,
                                 obnamlib.IDPATH_SKIP,
                                 time.time, 0, '')
        self.assertEqual(s2.list_clients(), ['foo'])
        
    def test_adding_existing_client_fails(self):
        self.repo.lock_root()
        self.repo.add_client('foo')
        self.assertRaises(obnamlib.Error, self.repo.add_client, 'foo')
        
    def test_removing_client_without_root_lock_fails(self):
        self.assertRaises(obnamlib.LockFail, self.repo.remove_client, 'foo')
        
    def test_removing_nonexistent_client_fails(self):
        self.repo.lock_root()
        self.assertRaises(obnamlib.Error, self.repo.remove_client, 'foo')
        
    def test_removing_client_works(self):
        self.repo.lock_root()
        self.repo.add_client('foo')
        self.repo.remove_client('foo')
        self.assertEqual(self.repo.list_clients(), [])
        
    def test_removing_client_persists_past_commit(self):
        self.repo.lock_root()
        self.repo.add_client('foo')
        self.repo.remove_client('foo')
        self.repo.commit_root()
        self.assertEqual(self.repo.list_clients(), [])

    def test_adding_client_without_commit_does_not_happen(self):
        self.repo.lock_root()
        self.repo.add_client('foo')
        self.repo.unlock_root()
        self.assertEqual(self.repo.list_clients(), [])

    def test_removing_client_without_commit_does_not_happen(self):
        self.repo.lock_root()
        self.repo.add_client('foo')
        self.repo.commit_root()
        self.repo.lock_root()
        self.repo.remove_client('foo')
        self.repo.unlock_root()
        self.assertEqual(self.repo.list_clients(), ['foo'])

    def test_removing_client_that_has_data_removes_the_data_as_well(self):
        self.repo.lock_root()
        self.repo.add_client('foo')
        self.repo.commit_root()

        self.repo.lock_client('foo')
        self.repo.lock_shared()
        self.repo.start_generation()
        self.repo.create('/', obnamlib.Metadata())
        self.repo.commit_client()
        self.repo.commit_shared()

        self.repo.lock_root()
        self.repo.remove_client('foo')
        self.repo.commit_root()

        self.assertEqual(self.repo.list_clients(), [])
        self.assertFalse(self.fs.exists('foo'))


class RepositoryClientTests(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

        self.fs = obnamlib.LocalFS(self.tempdir)
        self.repo = obnamlib.Repository(self.fs, obnamlib.DEFAULT_NODE_SIZE,
                                        obnamlib.DEFAULT_UPLOAD_QUEUE_SIZE,
                                        obnamlib.DEFAULT_LRU_SIZE, None,
                                        obnamlib.IDPATH_DEPTH,
                                        obnamlib.IDPATH_BITS,
                                        obnamlib.IDPATH_SKIP,
                                        time.time, 0, '')
        self.repo.lock_root()
        self.repo.add_client('client_name')
        self.repo.commit_root()
        
        self.otherfs = obnamlib.LocalFS(self.tempdir)
        self.other = obnamlib.Repository(self.otherfs, 
                                         obnamlib.DEFAULT_NODE_SIZE,
                                         obnamlib.DEFAULT_UPLOAD_QUEUE_SIZE,
                                         obnamlib.DEFAULT_LRU_SIZE, None,
                                         obnamlib.IDPATH_DEPTH,
                                         obnamlib.IDPATH_BITS,
                                         obnamlib.IDPATH_SKIP,
                                         time.time, 0, '')
        
        self.dir_meta = obnamlib.Metadata()
        self.dir_meta.st_mode = stat.S_IFDIR | 0777

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_has_not_got_client_lock(self):
        self.assertFalse(self.repo.got_client_lock)

    def test_locks_client(self):
        self.repo.lock_client('client_name')
        self.assert_(self.repo.got_client_lock)

    def test_locking_client_twice_fails(self):
        self.repo.lock_client('client_name')
        self.assertRaises(obnamlib.Error, self.repo.lock_client, 
                          'client_name')

    def test_locking_nonexistent_client_fails(self):
        self.assertRaises(obnamlib.LockFail, self.repo.lock_client, 'foo')

    def test_unlock_client_releases_lock(self):
        self.repo.lock_client('client_name')
        self.repo.unlock_client()
        self.assertFalse(self.repo.got_client_lock)

    def test_commit_client_releases_lock(self):
        self.repo.lock_client('client_name')
        self.repo.lock_shared()
        self.repo.commit_client()
        self.repo.commit_shared()
        self.assertFalse(self.repo.got_client_lock)

    def test_commit_does_not_mark_as_checkpoint_by_default(self):
        self.repo.lock_client('client_name')
        self.repo.lock_shared()
        self.repo.start_generation()
        genid = self.repo.new_generation
        self.repo.commit_client()
        self.repo.commit_shared()
        self.repo.open_client('client_name')
        self.assertFalse(self.repo.get_is_checkpoint(genid))

    def test_commit_marks_as_checkpoint_when_requested(self):
        self.repo.lock_client('client_name')
        self.repo.lock_shared()
        self.repo.start_generation()
        genid = self.repo.new_generation
        self.repo.commit_client(checkpoint=True)
        self.repo.commit_shared()

        self.repo.open_client('client_name')
        self.assert_(self.repo.get_is_checkpoint(genid))

    def test_commit_client_without_lock_fails(self):
        self.assertRaises(obnamlib.LockFail, self.repo.commit_client)
        
    def test_unlock_client_without_lock_fails(self):
        self.assertRaises(obnamlib.LockFail, self.repo.unlock_client)

    def test_commit_client_when_locked_by_other_fails(self):
        self.other.lock_client('client_name')
        self.assertRaises(obnamlib.LockFail, self.repo.commit_client)

    def test_unlock_client_when_locked_by_other_fails(self):
        self.other.lock_client('client_name')
        self.assertRaises(obnamlib.LockFail, self.repo.unlock_client)

    def test_opens_client_fails_if_client_does_not_exist(self):
        self.assertRaises(obnamlib.Error, self.repo.open_client, 'bad')

    def test_opens_client_even_when_locked_by_other(self):
        self.other.lock_client('client_name')
        self.repo.open_client('client_name')
        self.assert_(True)
        
    def test_lists_no_generations_when_readonly(self):
        self.repo.open_client('client_name')
        self.assertEqual(self.repo.list_generations(), [])
        
    def test_lists_no_generations_when_locked(self):
        self.repo.lock_client('client_name')
        self.assertEqual(self.repo.list_generations(), [])
        
    def test_listing_generations_fails_if_client_is_not_open(self):
        self.assertRaises(obnamlib.Error, self.repo.list_generations)

    def test_not_making_new_generation(self):
        self.assertEqual(self.repo.new_generation, None)

    def test_starting_new_generation_without_lock_fails(self):
        self.assertRaises(obnamlib.LockFail, self.repo.start_generation)

    def test_starting_new_generation_works(self):
        self.repo.lock_client('client_name')
        gen = self.repo.start_generation()
        self.assert_(self.repo.new_generation)
        self.assertEqual(self.repo.new_generation, gen)
        self.assertEqual(self.repo.list_generations(),  [gen])

    def test_starting_second_concurrent_new_generation_fails(self):
        self.repo.lock_client('client_name')
        self.repo.start_generation()
        self.assertRaises(obnamlib.Error, self.repo.start_generation)

    def test_second_generation_has_different_id_from_first(self):
        self.repo.lock_client('client_name')
        self.repo.lock_shared()
        gen = self.repo.start_generation()
        self.repo.commit_client()
        self.repo.commit_shared()
        self.repo.lock_client('client_name')
        self.assertNotEqual(gen, self.repo.start_generation())

    def test_new_generation_has_start_time_only(self):
        self.repo.lock_client('client_name')
        gen = self.repo.start_generation()
        start, end = self.repo.get_generation_times(gen)
        self.assertNotEqual(start, None)
        self.assertEqual(end, None)

    def test_commited_generation_has_start_and_end_times(self):
        self.repo.lock_client('client_name')
        self.repo.lock_shared()
        gen = self.repo.start_generation()
        self.repo.commit_client()
        self.repo.commit_shared()

        self.repo.open_client('client_name')
        start, end = self.repo.get_generation_times(gen)
        self.assertNotEqual(start, None)
        self.assertNotEqual(end, None)
        self.assert_(start <= end)

    def test_adding_generation_without_committing_does_not_add_it(self):
        self.repo.lock_client('client_name')
        self.repo.lock_shared()
        self.repo.start_generation()
        self.repo.unlock_client()
        self.repo.unlock_shared()
        self.repo.open_client('client_name')
        self.assertEqual(self.repo.list_generations(), [])

    def test_removing_generation_works(self):
        self.repo.lock_client('client_name')
        self.repo.lock_shared()
        gen = self.repo.start_generation()
        self.repo.commit_client()
        self.repo.commit_shared()

        self.repo.open_client('client_name')
        self.assertEqual(len(self.repo.list_generations()), 1)

        self.repo.lock_client('client_name')
        self.repo.lock_shared()
        self.repo.remove_generation(gen)
        self.repo.commit_client()
        self.repo.commit_shared()

        self.repo.open_client('client_name')
        self.assertEqual(self.repo.list_generations(), [])

    def test_removing_only_second_generation_works(self):
        # Create first generation. It will be empty.
        self.repo.lock_client('client_name')
        self.repo.lock_shared()
        gen1 = self.repo.start_generation()
        self.repo.commit_client()
        self.repo.commit_shared()

        # Create second generation. It will have a file with two chunks.
        # Only one of the chunks will be put into the shared trees.
        self.repo.lock_client('client_name')
        self.repo.lock_shared()
        gen2 = self.repo.start_generation()
        chunk_id1 = self.repo.put_chunk_only('data')
        self.repo.put_chunk_in_shared_trees(chunk_id1, 'checksum')
        chunk_id2 = self.repo.put_chunk_only('data2')
        self.repo.set_file_chunks('/foo', [chunk_id1, chunk_id2])
        self.repo.commit_client()
        self.repo.commit_shared()

        # Do we have the right generations? And the chunk2?
        self.repo.open_client('client_name')
        self.assertEqual(len(self.repo.list_generations()), 2)
        self.assertTrue(self.repo.chunk_exists(chunk_id1))
        self.assertTrue(self.repo.chunk_exists(chunk_id2))

        # Remove second generation. This should remove the chunk too.
        self.repo.lock_client('client_name')
        self.repo.lock_shared()
        self.repo.remove_generation(gen2)
        self.repo.commit_client()
        self.repo.commit_shared()

        # Make sure we have only the first generation, and that the
        # chunks are gone.
        self.repo.open_client('client_name')
        self.assertEqual(self.repo.list_generations(), [gen1])
        self.assertFalse(self.repo.chunk_exists(chunk_id1))
        self.assertFalse(self.repo.chunk_exists(chunk_id2))

    def test_removing_started_generation_fails(self):
        self.repo.lock_client('client_name')
        gen = self.repo.start_generation()
        self.assertRaises(obnamlib.Error,
                          self.repo.remove_generation, gen)

    def test_removing_without_committing_does_not_remove(self):
        self.repo.lock_client('client_name')
        self.repo.lock_shared()
        gen = self.repo.start_generation()
        self.repo.commit_client()
        self.repo.commit_shared()

        self.repo.lock_client('client_name')
        self.repo.lock_shared()
        self.repo.remove_generation(gen)
        self.repo.unlock_client()
        self.repo.unlock_shared()

        self.repo.open_client('client_name')
        self.assertEqual(self.repo.list_generations(), [gen])

    def test_new_generation_has_root_dir_only(self):
        self.repo.lock_client('client_name')
        gen = self.repo.start_generation()
        self.assertEqual(self.repo.listdir(gen, '/'), [])

    def test_create_fails_unless_generation_is_started(self):
        self.assertRaises(obnamlib.Error, self.repo.create, None, None)

    def test_create_adds_file(self):
        self.repo.lock_client('client_name')
        gen = self.repo.start_generation()
        self.repo.create('/', self.dir_meta)
        self.repo.create('/foo', obnamlib.Metadata())
        self.assertEqual(self.repo.listdir(gen, '/'), ['foo'])

    def test_create_adds_two_files(self):
        self.repo.lock_client('client_name')
        gen = self.repo.start_generation()
        self.repo.create('/', self.dir_meta)
        self.repo.create('/foo', obnamlib.Metadata())
        self.repo.create('/bar', obnamlib.Metadata())
        self.assertEqual(sorted(self.repo.listdir(gen, '/')), ['bar', 'foo'])

    def test_create_adds_lots_of_files(self):
        n = 100
        self.repo.lock_client('client_name')
        gen = self.repo.start_generation()
        pathnames = ['/%d' % i for i in range(n)]
        for pathname in pathnames:
            self.repo.create(pathname, obnamlib.Metadata())
        self.assertEqual(sorted(self.repo.listdir(gen, '/')), 
                         sorted(os.path.basename(x) for x in pathnames))

    def test_create_adds_dir(self):
        self.repo.lock_client('client_name')
        gen = self.repo.start_generation()
        self.repo.create('/foo', self.dir_meta)
        self.assertEqual(self.repo.listdir(gen, '/foo'), [])

    def test_create_adds_dir_after_file_in_it(self):
        self.repo.lock_client('client_name')
        gen = self.repo.start_generation()
        self.repo.create('/foo/bar', obnamlib.Metadata())
        self.repo.create('/foo', self.dir_meta)
        self.assertEqual(self.repo.listdir(gen, '/foo'), ['bar'])

    def test_gets_metadata_for_dir(self):
        self.repo.lock_client('client_name')
        gen = self.repo.start_generation()
        self.repo.create('/foo', self.dir_meta)
        self.assertEqual(self.repo.get_metadata(gen, '/foo').st_mode, 
                         self.dir_meta.st_mode)

    def test_remove_removes_file(self):
        self.repo.lock_client('client_name')
        gen = self.repo.start_generation()
        self.repo.create('/foo', obnamlib.Metadata())
        self.repo.remove('/foo')
        self.assertEqual(self.repo.listdir(gen, '/'), [])

    def test_remove_removes_directory_tree(self):
        self.repo.lock_client('client_name')
        gen = self.repo.start_generation()
        self.repo.create('/foo/bar', obnamlib.Metadata())
        self.repo.remove('/foo')
        self.assertEqual(self.repo.listdir(gen, '/'), [])

    def test_get_metadata_works(self):
        metadata = obnamlib.Metadata()
        metadata.st_size = 123
        self.repo.lock_client('client_name')
        gen = self.repo.start_generation()
        self.repo.create('/foo', metadata)
        received = self.repo.get_metadata(gen, '/foo')
        self.assertEqual(metadata.st_size, received.st_size)

    def test_get_metadata_raises_exception_if_file_does_not_exist(self):
        self.repo.lock_client('client_name')
        gen = self.repo.start_generation()
        self.assertRaises(obnamlib.Error, self.repo.get_metadata,
                          gen, '/foo')


class RepositoryChunkTests(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

        self.fs = obnamlib.LocalFS(self.tempdir)
        self.repo = obnamlib.Repository(self.fs, obnamlib.DEFAULT_NODE_SIZE,
                                        obnamlib.DEFAULT_UPLOAD_QUEUE_SIZE,
                                        obnamlib.DEFAULT_LRU_SIZE, None,
                                        obnamlib.IDPATH_DEPTH,
                                        obnamlib.IDPATH_BITS,
                                        obnamlib.IDPATH_SKIP,
                                        time.time, 0, '')
        self.repo.lock_root()
        self.repo.add_client('client_name')
        self.repo.commit_root()
        self.repo.lock_client('client_name')
        self.repo.start_generation()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_checksum_returns_checksum(self):
        self.assertNotEqual(self.repo.checksum('data'), None)

    def test_put_chunk_returns_id(self):
        self.repo.lock_shared()
        self.assertNotEqual(self.repo.put_chunk_only('data'), None)
        
    def test_get_chunk_retrieves_what_put_chunk_puts(self):
        self.repo.lock_shared()
        chunkid = self.repo.put_chunk_only('data')
        self.assertEqual(self.repo.get_chunk(chunkid), 'data')
        
    def test_chunk_does_not_exist(self):
        self.assertFalse(self.repo.chunk_exists(1234))
        
    def test_chunk_exists_after_it_is_put(self):
        self.repo.lock_shared()
        chunkid = self.repo.put_chunk_only('chunk')
        self.assert_(self.repo.chunk_exists(chunkid))

    def test_removes_chunk(self):
        self.repo.lock_shared()
        chunkid = self.repo.put_chunk_only('chunk')
        self.repo.remove_chunk(chunkid)
        self.assertFalse(self.repo.chunk_exists(chunkid))

    def test_silently_ignores_failure_when_removing_nonexistent_chunk(self):
        self.repo.lock_shared()
        self.assertEqual(self.repo.remove_chunk(0), None)
        
    def test_find_chunks_finds_what_put_chunk_puts(self):
        self.repo.lock_shared()
        checksum = self.repo.checksum('data')
        chunkid = self.repo.put_chunk_only('data')
        self.repo.put_chunk_in_shared_trees(chunkid, checksum)
        self.assertEqual(self.repo.find_chunks(checksum), [chunkid])
        
    def test_find_chunks_finds_nothing_if_nothing_is_put(self):
        self.assertEqual(self.repo.find_chunks('checksum'), [])
        
    def test_handles_checksum_collision(self):
        self.repo.lock_shared()
        checksum = self.repo.checksum('data')
        chunkid1 = self.repo.put_chunk_only('data')
        chunkid2 = self.repo.put_chunk_only('data')
        self.repo.put_chunk_in_shared_trees(chunkid1, checksum)
        self.repo.put_chunk_in_shared_trees(chunkid2, checksum)
        self.assertEqual(set(self.repo.find_chunks(checksum)),
                         set([chunkid1, chunkid2]))

    def test_returns_no_chunks_initially(self):
        self.assertEqual(self.repo.list_chunks(), [])
        
    def test_returns_chunks_after_they_exist(self):
        self.repo.lock_shared()
        checksum = self.repo.checksum('data')
        chunkids = []
        for i in range(2):
            chunkids.append(self.repo.put_chunk_only('data'))
        self.assertEqual(sorted(self.repo.list_chunks()), sorted(chunkids))


class RepositoryGetSetChunksTests(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

        self.fs = obnamlib.LocalFS(self.tempdir)
        self.repo = obnamlib.Repository(self.fs, obnamlib.DEFAULT_NODE_SIZE,
                                        obnamlib.DEFAULT_UPLOAD_QUEUE_SIZE,
                                        obnamlib.DEFAULT_LRU_SIZE, None,
                                        obnamlib.IDPATH_DEPTH,
                                        obnamlib.IDPATH_BITS,
                                        obnamlib.IDPATH_SKIP,
                                        time.time, 0, '')
        self.repo.lock_root()
        self.repo.add_client('client_name')
        self.repo.commit_root()
        self.repo.lock_client('client_name')
        self.gen = self.repo.start_generation()
        self.repo.create('/foo', obnamlib.Metadata())

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_file_has_no_chunks(self):
        self.assertEqual(self.repo.get_file_chunks(self.gen, '/foo'), [])

    def test_sets_chunks_for_file(self):
        self.repo.set_file_chunks('/foo', [1, 2])
        chunkids = self.repo.get_file_chunks(self.gen, '/foo')
        self.assertEqual(sorted(chunkids), [1, 2])

    def test_appends_chunks_to_empty_list(self):
        self.repo.append_file_chunks('/foo', [1, 2])
        chunkids = self.repo.get_file_chunks(self.gen, '/foo')
        self.assertEqual(sorted(chunkids), [1, 2])

    def test_appends_chunks_to_nonempty_list(self):
        self.repo.append_file_chunks('/foo', [1, 2])
        self.repo.append_file_chunks('/foo', [3, 4])
        chunkids = self.repo.get_file_chunks(self.gen, '/foo')
        self.assertEqual(sorted(chunkids), [1, 2, 3, 4])


class RepositoryGenspecTests(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

        repodir = os.path.join(self.tempdir, 'repo')
        os.mkdir(repodir)
        fs = obnamlib.LocalFS(repodir)
        self.repo = obnamlib.Repository(fs, obnamlib.DEFAULT_NODE_SIZE,
                                        obnamlib.DEFAULT_UPLOAD_QUEUE_SIZE,
                                        obnamlib.DEFAULT_LRU_SIZE, None,
                                        obnamlib.IDPATH_DEPTH,
                                        obnamlib.IDPATH_BITS,
                                        obnamlib.IDPATH_SKIP,
                                        time.time, 0, '')
        self.repo.lock_root()
        self.repo.add_client('client_name')
        self.repo.commit_root()
        self.repo.lock_client('client_name')
        self.repo.lock_shared()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def backup(self):
        gen = self.repo.start_generation()
        self.repo.commit_client()
        self.repo.commit_shared()
        self.repo.lock_client('client_name')
        self.repo.lock_shared()
        return gen

    def test_latest_raises_error_if_there_are_no_generations(self):
        self.assertRaises(obnamlib.Error, self.repo.genspec, 'latest')

    def test_latest_returns_only_generation(self):
        gen = self.backup()
        self.assertEqual(self.repo.genspec('latest'), gen)

    def test_latest_returns_newest_generation(self):
        self.backup()
        gen = self.backup()
        self.assertEqual(self.repo.genspec('latest'), gen)

    def test_other_spec_returns_itself(self):
        gen = self.backup()
        self.assertEqual(self.repo.genspec(str(gen)), gen)

    def test_noninteger_spec_raises_error(self):
        gen = self.backup()
        self.assertNotEqual(gen, 'foo')
        self.assertRaises(obnamlib.Error, self.repo.genspec, 'foo')

    def test_nonexistent_spec_raises_error(self):
        self.backup()
        self.assertRaises(obnamlib.Error, self.repo.genspec, 1234)


class RepositoryWalkTests(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

        self.fs = obnamlib.LocalFS(self.tempdir)
        self.repo = obnamlib.Repository(self.fs, obnamlib.DEFAULT_NODE_SIZE,
                                        obnamlib.DEFAULT_UPLOAD_QUEUE_SIZE,
                                        obnamlib.DEFAULT_LRU_SIZE, None,
                                        obnamlib.IDPATH_DEPTH,
                                        obnamlib.IDPATH_BITS,
                                        obnamlib.IDPATH_SKIP,
                                        time.time, 0, '')
        self.repo.lock_root()
        self.repo.add_client('client_name')
        self.repo.commit_root()

        self.dir_meta = obnamlib.Metadata()
        self.dir_meta.st_mode = stat.S_IFDIR | 0777
        
        self.file_meta = obnamlib.Metadata()
        self.file_meta.st_mode = stat.S_IFREG | 0644
        
        self.repo.lock_client('client_name')
        self.repo.lock_shared()
        self.gen = self.repo.start_generation()
        
        self.repo.create('/', self.dir_meta)
        self.repo.create('/foo', self.dir_meta)
        self.repo.create('/foo/bar', self.file_meta)
        
        self.repo.commit_client()
        self.repo.open_client('client_name')

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_walk_find_everything(self):
        found = list(self.repo.walk(self.gen, '/'))
        self.assertEqual(found,
                         [('/', self.dir_meta),
                          ('/foo', self.dir_meta),
                          ('/foo/bar', self.file_meta)])

    def test_walk_find_depth_first(self):
        found = list(self.repo.walk(self.gen, '/', depth_first=True))
        self.assertEqual(found,
                         [('/foo/bar', self.file_meta),
                          ('/foo', self.dir_meta),
                          ('/', self.dir_meta)])

