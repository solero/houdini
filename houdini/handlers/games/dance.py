from houdini import handlers
from houdini.handlers import XTPacket
from houdini.data.dance import DanceSongCollection
from houdini.penguin import Penguin

import random
import time
import asyncio
import itertools

from dataclasses import dataclass


@dataclass
class Dancer:
    penguin: Penguin
    score: int
    difficulty: int


class DanceFloor:
    Easy = 0
    Medium = 1
    Difficult = 2
    Expert = 3

    Capacity = 15

    DanceRoomId = 952

    def __init__(self, server):
        self.server = server

        self._queue = {}
        self._dancers = {}

        self._tracks = itertools.cycle(server.dance_songs.values())
        self._queued_track = next(self._tracks)
        self._current_track = None

        self._next_song_timestamp = 0

    async def add_penguin(self, p):
        if p.id not in self._queue and p.id not in self._dancers:
            if len(self._queue) < DanceFloor.Capacity:
                self._queue[p.id] = Dancer(penguin=p, score=0, difficulty=DanceFloor.Easy)
                await p.send_xt('gz', 0, self._queued_track.id, self.get_time_to_next_song())
                await p.send_xt('jz', 'true', self._queued_track.id, self.get_time_to_next_song())
            else:
                await p.send_xt('jz', 'false')

    async def remove_penguin(self, p):
        self._queue.pop(p.id, None)

        if p.id in self._dancers:
            self._dancers.pop(p.id)
            await self.send_xt('zm', self.get_string())

    async def start(self):
        while True:
            await self.next_round()
            await asyncio.sleep(self._current_track.song_length_millis // 1000)

    async def next_round(self):
        self._current_track = self._queued_track

        self._dancers = self._queue
        self._queue = {}

        song_data = {
            difficulty: DanceFloor._get_song_data(
                self._current_track.song_length, self._current_track.millis_per_bar, difficulty
            ) for difficulty in [
                DanceFloor.Easy, DanceFloor.Medium, DanceFloor.Difficult, DanceFloor.Expert
            ]}

        for dancer in self._dancers.values():
            note_types, note_times, note_lengths = song_data[dancer.difficulty]
            await dancer.penguin.send_xt(
                'sz',
                ','.join(map(str, note_times)),
                ','.join(map(str, note_types)),
                ','.join(map(str, note_lengths)),
                self._current_track.millis_per_bar
            )

        await self.send_xt('zm', self.get_string())

        self._queued_track = next(self._tracks)
        self._next_song_timestamp = int(round(time.time() * 1000)) + self._current_track.song_length_millis

    async def send_xt(self, *data):
        for dancer in self._dancers.values():
            await dancer.penguin.send_xt(*data)

    def set_difficulty(self, p, difficulty):
        self._queue[p.id].difficulty = max(0, min(difficulty, DanceFloor.Expert))

    def set_score(self, p, score):
        self._dancers[p.id].score = max(self._dancers[p.id].score, score)

    def get_string(self):
        return ','.join(f'-1|{dancer.penguin.safe_name}|{dancer.score}' for dancer in self._dancers.values())

    def get_time_to_next_song(self):
        return self._next_song_timestamp - int(round(time.time() * 1000))

    @classmethod
    def _get_song_data(cls, song_length, millis_per_bar, difficulty):
        millis_per_beat = millis_per_bar // 4

        note_types = []
        note_times = []
        note_lengths = []
        last_note_times = [0, 0, 0, 0]

        def add_note(beat_time, max_length):
            note_type = random.randrange(4)
            note_time = int(beat_time * millis_per_beat)
            note_length = int(random.randint(0, max_length) * millis_per_beat)
            if note_time > last_note_times[note_type]:
                note_types.append(note_type)
                note_times.append(note_time)
                note_lengths.append(note_length)
                last_note_times[note_type] = note_time + note_length

        for song_time in range(4, song_length):
            if not song_time % 8 and difficulty >= cls.Easy:
                add_note(song_time, 4)
                if random.randrange(2) == 0:
                    add_note(song_time, 0)
            elif not song_time % 4 and difficulty >= cls.Medium:
                add_note(song_time, 4)
                if random.randrange(4) == 0:
                    add_note(song_time, 0)
            elif not song_time % 2 and difficulty >= cls.Difficult:
                add_note(song_time, 2)
            elif random.randrange(4) > 0 and difficulty >= cls.Expert:
                add_note(song_time, 0)
                if random.randrange(4) == 0:
                    add_note(song_time + 0.5, 0)

        return note_types, note_times, note_lengths


@handlers.boot
async def songs_load(server):
    server.dance_songs = await DanceSongCollection.get_collection()
    server.logger.info(f'Loaded {len(server.dance_songs)} dance tracks')

    server.dance_floor = DanceFloor(server)
    asyncio.create_task(server.dance_floor.start())


@handlers.handler(XTPacket('gz', ext='z'))
@handlers.player_in_room(DanceFloor.DanceRoomId)
async def handle_get_game(p):
    await p.server.dance_floor.add_penguin(p)


@handlers.handler(XTPacket('zr', ext='z'))
@handlers.player_in_room(DanceFloor.DanceRoomId)
async def handle_get_game_again(p):
    await p.server.dance_floor.add_penguin(p)


@handlers.handler(XTPacket('zd', ext='z'))
@handlers.player_in_room(DanceFloor.DanceRoomId)
async def handle_change_difficulty(p, difficulty: int):
    p.server.dance_floor.set_difficulty(p, difficulty)


@handlers.handler(XTPacket('zm', ext='z'))
@handlers.player_in_room(DanceFloor.DanceRoomId)
async def handle_send_move(p, score: int):
    p.server.dance_floor.set_score(p, score)
    await p.server.dance_floor.send_xt('zm', p.server.dance_floor.get_string())


@handlers.handler(XTPacket('cz', ext='z'))
@handlers.player_in_room(DanceFloor.DanceRoomId)
async def handle_leave_game(p):
    await p.server.dance_floor.remove_penguin(p)


@handlers.disconnected
@handlers.player_attribute(joined_world=True)
async def handle_disconnect_dance_floor(p):
    await p.server.dance_floor.remove_penguin(p)
