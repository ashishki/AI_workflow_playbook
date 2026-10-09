#!/usr/bin/env python3
"""Local synthetic booking demo. Python standard library only."""
import argparse
import contextlib
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import re
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
import uuid

ROOT = Path(__file__).resolve().parent
TEACHERS = frozenset({'anna', 'boris'})
MAX_BODY = 16384
UNCERTAIN_WRITE = 'Результат сохранения неопределён. Повторите тот же request_id; новый запрос может создать другую запись.'
UNAVAILABLE_STORE = ('Данные недоступны после ошибки сохранения; результат операции неопределён. '
                     'Остановите сервер, проверьте или восстановите JSON и запустите снова; '
                     'затем повторите тот же request_id.')


class APIError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message


def decode_json(raw):
    def reject_constant(value):
        raise ValueError('Non-JSON constant: ' + value)
    return json.loads(raw, parse_constant=reject_constant)


def validated_request(payload):
    if not isinstance(payload, dict):
        raise APIError(400, 'Ожидается JSON-объект.')
    fields = {}
    for name, limit, label in [('student', 100, 'имя ученика'), ('request_id', 128, 'request_id')]:
        value = payload.get(name)
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
            raise APIError(400, f'Укажите {label}: от 1 до {limit} символов.')
        fields[name] = value.strip()
    day = payload.get('date')
    if not isinstance(day, str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', day):
        raise APIError(400, 'Дата должна иметь формат ГГГГ-ММ-ДД.')
    try:
        dt.date.fromisoformat(day)
    except ValueError:
        raise APIError(400, 'Такой календарной даты не существует.')
    slot = payload.get('slot')
    if not isinstance(slot, str) or not re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]', slot):
        raise APIError(400, 'Время должно иметь формат ЧЧ:ММ (00:00–23:59).')
    fields.update(date=day, slot=slot)
    return fields


def validate_document(document):
    if not isinstance(document, dict) or document.get('version') != 1 or not isinstance(document.get('bookings'), list):
        raise ValueError('Expected version 1 booking document')
    ids, requests, occupied = set(), set(), set()
    result = []
    for booking in document['bookings']:
        if not isinstance(booking, dict) or booking.get('teacher') not in TEACHERS:
            raise ValueError('Invalid teacher in stored booking')
        try:
            fields = validated_request(booking)
        except APIError as error:
            raise ValueError(error.message) from error
        booking_id, created = booking.get('id'), booking.get('created_at')
        if not isinstance(booking_id, str) or not booking_id or not isinstance(created, str):
            raise ValueError('Invalid booking id or timestamp')
        try:
            dt.datetime.fromisoformat(created)
        except ValueError as error:
            raise ValueError('Invalid booking timestamp') from error
        teacher = booking['teacher']
        request_key = (teacher, fields['request_id'])
        slot_key = (teacher, fields['date'], fields['slot'])
        if booking_id in ids or request_key in requests or slot_key in occupied:
            raise ValueError('Duplicate booking, request or teacher slot in stored data')
        ids.add(booking_id)
        requests.add(request_key)
        occupied.add(slot_key)
        result.append(dict(fields, id=booking_id, teacher=teacher, created_at=created))
    return {'version': 1, 'bookings': result}


def atomic_json(path, document):
    """Replace only after a complete fsynced temporary file has been written."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix='.' + path.name + '.', delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(document, handle, ensure_ascii=False, indent=2)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


@contextlib.contextmanager
def exclusive_data_lock(data_path):
    """One process owns a data file; threads are serialized separately by Store."""
    data_path = Path(data_path)
    data_path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(data_path) + '.lock', 'a') as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError('Data is in use: stop the server before maintenance.') from error
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.lock = threading.RLock()
        self.available = True
        if self.path.exists():
            self.document = validate_document(decode_json(self.path.read_text(encoding='utf-8')))
        else:
            self.document = {'version': 1, 'bookings': []}
            atomic_json(self.path, self.document)

    def require_available(self):
        if not self.available:
            raise APIError(503, UNAVAILABLE_STORE)

    def reconcile_after_write_failure(self):
        # os.replace may have committed before a later fsync/cleanup failure.
        # Discard the cache first: a failed reload must never leave stale data usable.
        self.available = False
        self.document = None
        try:
            actual = validate_document(decode_json(self.path.read_text(encoding='utf-8')))
        except Exception:
            return False
        self.document = actual
        self.available = True
        return True

    def list(self, teacher):
        with self.lock:
            self.require_available()
            return sorted((b.copy() for b in self.document['bookings'] if b['teacher'] == teacher),
                          key=lambda b: (b['date'], b['slot'], b['id']))

    def get(self, teacher, booking_id):
        with self.lock:
            self.require_available()
            for booking in self.document['bookings']:
                if booking['id'] == booking_id and booking['teacher'] == teacher:
                    return booking.copy()
        raise APIError(404, 'Запись не найдена.')

    def create(self, teacher, payload):
        with self.lock:
            self.require_available()
            fields = validated_request(payload)
            for booking in self.document['bookings']:
                if booking['teacher'] == teacher and booking['request_id'] == fields['request_id']:
                    return booking.copy(), False
            # Apply the new schedule only to creation, after legacy replay lookup.
            # Stored-document validation must continue accepting every valid HH:MM.
            if fields['slot'][-2:] not in {'00', '30'}:
                raise APIError(400, 'Для новой записи выберите время с минутами 00 или 30, например 09:00 или 09:30.')
            for booking in self.document['bookings']:
                if (booking['teacher'], booking['date'], booking['slot']) == (teacher, fields['date'], fields['slot']):
                    raise APIError(409, 'Это время уже занято. Выберите другое время.')
            booking = dict(fields, id=str(uuid.uuid4()), teacher=teacher,
                           created_at=dt.datetime.now(dt.timezone.utc).isoformat())
            updated = {'version': 1, 'bookings': self.document['bookings'] + [booking]}
            try:
                atomic_json(self.path, updated)
            except Exception as error:
                recovered = self.reconcile_after_write_failure()
                raise APIError(503, UNCERTAIN_WRITE if recovered else UNAVAILABLE_STORE) from error
            self.document = updated
            return booking.copy(), True


class BookingServer(ThreadingHTTPServer):
    daemon_threads = False
    block_on_close = True


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, content, content_type='application/json; charset=utf-8'):
        raw = (json.dumps(content, ensure_ascii=False).encode('utf-8')
               if content_type.startswith('application/json') else content)
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(raw)

    def teacher(self):
        value = self.headers.get('X-Teacher')
        if value not in TEACHERS or len(self.headers.get_all('X-Teacher', [])) != 1:
            raise APIError(403, 'Выберите преподавателя: anna или boris (демо-идентификация).')
        return value

    def do_GET(self):
        path = urlsplit(self.path).path
        try:
            if path == '/api/bookings':
                self.respond(200, {'bookings': self.server.store.list(self.teacher())})
            elif path.startswith('/api/bookings/'):
                self.respond(200, {'booking': self.server.store.get(self.teacher(), path[len('/api/bookings/'):])})
            elif path.startswith('/api/'):
                self.teacher()
                raise APIError(404, 'Адрес не найден.')
            elif path in {'/', '/app.js', '/style.css'}:
                filename, mime = {'/': ('index.html', 'text/html; charset=utf-8'),
                                  '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                                  '/style.css': ('style.css', 'text/css; charset=utf-8')}[path]
                self.respond(200, (ROOT / 'web' / filename).read_bytes(), mime)
            else:
                raise APIError(404, 'Адрес не найден.')
        except APIError as error:
            self.respond(error.status, {'error': error.message})

    def do_POST(self):
        try:
            teacher = self.teacher()
            if urlsplit(self.path).path != '/api/bookings':
                raise APIError(404, 'Адрес не найден.')
            try:
                length = int(self.headers.get('Content-Length', '0'))
            except ValueError:
                raise APIError(400, 'Некорректная длина запроса.')
            if not 0 < length <= MAX_BODY:
                raise APIError(400 if length <= 0 else 413, 'JSON-запрос пуст или слишком большой.')
            self.connection.settimeout(10)
            try:
                payload = decode_json(self.rfile.read(length).decode('utf-8'))
            except (ValueError, UnicodeError):
                raise APIError(400, 'Некорректный JSON.')
            booking, created = self.server.store.create(teacher, payload)
            self.respond(201 if created else 200, {'booking': booking, 'replayed': not created})
        except APIError as error:
            self.respond(error.status, {'error': error.message})
        except (OSError, TimeoutError):
            self.respond(503, {'error': UNCERTAIN_WRITE})

    def log_message(self, format, *args):
        # Standard request metadata only; never log student names or JSON bodies.
        super().log_message(format, *args)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    serve = sub.add_parser('serve')
    serve.add_argument('--port', type=int, default=8765)
    for name in ('export', 'backup', 'restore', 'retire', 'resume'):
        command = sub.add_parser(name)
        if name in ('export', 'backup', 'retire'):
            command.add_argument('--output', type=Path, required=True)
        if name == 'restore':
            command.add_argument('--input', type=Path, required=True)
    for command in sub.choices.values():
        command.add_argument('--data', type=Path, default=ROOT / 'data' / 'bookings.json')
    args = parser.parse_args()
    data_path = args.data.resolve()
    retired = Path(str(data_path) + '.retired')
    try:
        if args.command in ('export', 'backup', 'retire'):
            output = args.output.resolve()
            lock_path = Path(str(data_path) + '.lock')
            reserved = {retired, lock_path, retired.resolve(), lock_path.resolve()}
            checkpoint_path = (output.parent == data_path.parent and
                               output.name.startswith(data_path.name + '.before-restore-'))
            if output in reserved or checkpoint_path:
                # Validate before opening/creating the data lock or any other file.
                raise RuntimeError('Export output is a reserved lifecycle metadata path.')
        with exclusive_data_lock(data_path):
            if args.command == 'serve':
                if retired.exists():
                    raise RuntimeError('This copy is retired; use resume explicitly to reopen it.')
                with BookingServer(('127.0.0.1', args.port), Handler) as server:
                    server.store = Store(data_path)
                    print(f'Local demo: http://127.0.0.1:{server.server_port} — X-Teacher is demo identity, not login.', flush=True)
                    try:
                        server.serve_forever()
                    except KeyboardInterrupt:
                        print('Stopped; JSON data preserved.', flush=True)
            elif args.command in ('export', 'backup', 'retire'):
                document = validate_document(decode_json(data_path.read_text(encoding='utf-8')))
                output = args.output.resolve()
                if output == data_path or output.exists():
                    raise RuntimeError('Export path must be new and different from the data file.')
                atomic_json(output, document)
                if args.command == 'retire':
                    retired.write_text('Local copy retired; source and data retained. No external services exist.\n', encoding='utf-8')
                print(f'{args.command}: {len(document["bookings"])} bookings exported to {output}', flush=True)
            elif args.command == 'restore':
                document = validate_document(decode_json(args.input.read_text(encoding='utf-8')))
                if data_path.exists():
                    checkpoint = Path(str(data_path) + '.before-restore-' + uuid.uuid4().hex + '.json')
                    checkpoint.write_bytes(data_path.read_bytes())
                    print(f'Previous data preserved at {checkpoint}', flush=True)
                atomic_json(data_path, document)
                print(f'Restored {len(document["bookings"])} bookings to {data_path}', flush=True)
            elif args.command == 'resume':
                retired.unlink(missing_ok=True)
                print('Local copy reopened; start serve explicitly.', flush=True)
    except (ValueError, OSError, RuntimeError) as error:
        parser.exit(1, f'Error: {error}\n')


if __name__ == '__main__':
    main()
