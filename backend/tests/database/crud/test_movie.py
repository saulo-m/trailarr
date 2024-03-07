from contextlib import contextmanager
from functools import wraps
from importlib import reload
import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine
import backend.database.crud.connection as connectionCRUD
import backend.database.crud.movie as movieCRUD
from backend.database.models.connection import ArrType, ConnectionCreate, MonitorType
from backend.database.models.movie import (
    # MovieBase,
    MovieCreate,
    MovieUpdate,
    # MovieRead,
)

# from backend.exceptions import InvalidResponseError

# Copied from backend/database/crud/movie.py
NO_MOVIE_MESSAGE = "Movie not found. Movie id: {} does not exist!"


# Default movie object to use in tests
movie = MovieCreate(
    connection_id=1,
    radarr_id=1,
    title="Movie Title",
    year=2021,
    # runtime=120,
    # website="http://example.com",
    # youtube_trailer_id="youtube_id",
    # folder_path="/path/to/folder",
    imdb_id="tt12345678",
    tmdb_id="123456",
    # poster_url="http://example.com/poster",
    # fanart_url="http://example.com/fanart",
    # poster_path="/path/to/poster",
    # fanart_path="/path/to/fanart",
    # trailer_exists=True,
    # monitor=True,
    # radarr_monitored=True,
)

# Default movie update object to use in tests
movie_update = MovieUpdate(
    monitor=True,
    radarr_monitored=True,
)

# Default movie id for create
MOVIE_ID_1 = 1

# Default movie id for failed read/update/delete
MOVIE_ID_2 = 2


# Setup the in-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
)
SQLModel.metadata.create_all(engine)


@contextmanager
def get_session():
    with Session(engine) as session:
        try:
            yield session
        finally:
            session.close()


def mock_manage_session(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Check if a '_session' keyword argument was provided
        if kwargs.get("_session") is None:
            # If not, create a new session and add it to kwargs
            with get_session() as _session:
                kwargs["_session"] = _session
                return func(*args, **kwargs)
        else:
            # If a session was provided, just call the function
            return func(*args, **kwargs)

    return wrapper


class TestMovieDatabaseHandler:
    movie_handler = movieCRUD.MovieDatabaseHandler()
    conn_handler = connectionCRUD.ConnectionDatabaseHandler()

    @pytest.fixture(autouse=True)
    def session_fixture(self, monkeypatch):
        # Monkeypatch the manage_session decorator
        monkeypatch.setattr(
            "backend.database.utils.engine.manage_session",
            mock_manage_session,
        )
        # Reload the connectionCRUD module to apply the monkeypatch to decorator
        reload(connectionCRUD)
        reload(movieCRUD)
        self.movie_handler = movieCRUD.MovieDatabaseHandler()
        self.conn_handler = connectionCRUD.ConnectionDatabaseHandler()

        # Mock the validate_connection function to return a success message
        monkeypatch.setattr(
            "backend.database.crud.connection.validate_connection",
            lambda _: "Success message",
        )
        # Call the create_connection method to use in tests
        # Default connection object to use in tests
        connection = ConnectionCreate(
            name="Connection Name",
            type=ArrType.RADARR,
            url="http://example.com",
            api_key="API_KEY",
            monitor=MonitorType.MONITOR_NEW,
        )
        self.conn_handler.create(connection)

    def test_create_success(self):
        # Call the create method and assert the return value
        assert self.movie_handler.create(movie) is True

    def test_create_failed(self):
        # Set the radarr_id to None to cause a validation error
        movie2 = movie.model_copy()
        movie2.radarr_id = None  # type: ignore
        # Call the create method and assert the return value
        with pytest.raises(Exception) as exc_info:
            self.movie_handler.create(movie2)
        assert exc_info.type.__name__ == "ValidationError"

    def test_create_failed_radarr_id_not_unique(self):
        # Create a movie
        movie2 = MovieCreate(connection_id=1, radarr_id=2, title="Movie Title 3")
        self.movie_handler.create(movie2)

        # Call the create method for same movie and assert the exception
        with pytest.raises(Exception) as exc_info:
            self.movie_handler.create(movie2)
        assert exc_info.type.__name__ == "ItemExistsError"

    def test_create_failed_connection_id_not_exists(self):
        # Set the connection_id to a non-existent connection
        movie2 = movie.model_copy()
        movie2.connection_id = 200
        # Call the create method and assert the return value
        with pytest.raises(Exception) as exc_info:
            self.movie_handler.create(movie2)
        assert exc_info.type.__name__ == "ItemNotFoundError"

    def test_create_bulk_success(self):
        # Call the create method and assert the return value
        movie2 = MovieCreate(connection_id=1, radarr_id=200, title="Movie Title 200")
        movie3 = MovieCreate(connection_id=1, radarr_id=201, title="Movie Title 201")
        assert self.movie_handler.create_bulk([movie2, movie3]) is True

    def test_create_bulk_failed(self):
        # Call the create method and assert the return value
        # Set the radarr_id to None to cause a validation error
        movie2 = movie.model_copy()
        movie2.radarr_id = None  # type: ignore
        with pytest.raises(Exception) as exc_info:
            self.movie_handler.create_bulk([movie2])
        assert exc_info.type.__name__ == "ValidationError"

    def test_create_bulk_failed_exists(self):
        # Create a movie to test the exists error
        movie2 = MovieCreate(connection_id=1, radarr_id=210, title="Movie Title 200")
        movie3 = MovieCreate(connection_id=1, radarr_id=211, title="Movie Title 201")
        assert self.movie_handler.create_bulk([movie2, movie3]) is True
        # Call the create method with same ids and assert the exception
        movie4 = MovieCreate(connection_id=1, radarr_id=211, title="Movie Title 201")
        with pytest.raises(Exception) as exc_info:
            self.movie_handler.create_bulk([movie4])
        assert exc_info.type.__name__ == "ItemExistsError"

    def test_create_or_update_bulk_success(self):
        # Create a movie to update later
        movie2 = MovieCreate(connection_id=1, radarr_id=202, title="Movie Title 200")
        assert self.movie_handler.create(movie2) is True
        movie2.title = "Movie Title 202"

        # Create another MovieCreate object to add
        movie3 = MovieCreate(connection_id=1, radarr_id=20, title="Movie Title 2")
        # Call the create method and assert the return value

        assert self.movie_handler.create_or_update_bulk([movie2, movie3]) is True

    def test_create_or_update_bulk_failed(self):
        # Call the create method and assert the return value
        # Set the connection_id to 2 to raise an ItemNotFoundError
        movie2 = movie.model_copy()
        movie2.connection_id = 200

        with pytest.raises(Exception) as exc_info:
            self.movie_handler.create_or_update_bulk([movie, movie2])
        assert exc_info.type.__name__ == "ItemNotFoundError"

    def test_read_success(self):
        # Create a movie to read
        assert self.movie_handler.create_or_update_bulk([movie]) is True

        # Call the read_movie method and assert the return value
        movie_read = self.movie_handler.read(MOVIE_ID_1)
        assert movie_read is not None
        assert movie_read.connection_id == movie.connection_id
        assert movie_read.radarr_id == movie.radarr_id
        assert movie_read.title == movie.title
        assert movie_read.year == movie.year
        assert movie_read.imdb_id == movie.imdb_id
        assert movie_read.tmdb_id == movie.tmdb_id
        assert movie_read.monitor is False

    def test_read_failed(self):
        # Call the read_movie method and assert the return value
        with pytest.raises(Exception) as exc_info:
            self.movie_handler.read(2000)
        assert exc_info.type.__name__ == "ItemNotFoundError"
        assert str(exc_info.value) == NO_MOVIE_MESSAGE.format(2000)

    def test_read_all_success(self):
        # Create a movie to read
        movie2 = MovieCreate(connection_id=1, radarr_id=203, title="Movie Title 200")
        assert self.movie_handler.create(movie2) is True

        # Call the read_all_movies method and assert the return value
        movie_read = self.movie_handler.read_all()
        assert len(movie_read) >= 1

    def test_read_all_by_connection_success(self):
        # Create a movie to read
        movie2 = MovieCreate(connection_id=1, radarr_id=204, title="Movie Title 200")
        assert self.movie_handler.create(movie2) is True

        # Call the read_all_movies method and assert the return value
        movie_read = self.movie_handler.read_all_by_connection(movie.connection_id)
        assert len(movie_read) >= 1

    def test_read_recent_success(self):
        # Create a movie to read
        movie2 = MovieCreate(connection_id=1, radarr_id=205, title="Movie Title 200")
        assert self.movie_handler.create(movie2) is True

        # Call the read_recent_movies method and assert the return value
        movie_read = self.movie_handler.read_recent()
        assert len(movie_read) >= 1

    def test_search_success(self):
        # Create a movie to read
        movie2 = MovieCreate(connection_id=1, radarr_id=206, title="Movie Title 200")
        assert self.movie_handler.create(movie2) is True

        # Call the search_movies method and assert the return value
        movie_read = self.movie_handler.search(movie.title)
        assert len(movie_read) >= 1

    def test_search_imdb_id_success(self):
        # Create a movie to read
        movie2 = MovieCreate(
            connection_id=1,
            radarr_id=207,
            title="Movie Title 200",
            imdb_id="tt12345689",
            tmdb_id="123457",
            year=2022,
        )
        assert self.movie_handler.create(movie2) is True

        # Call the search_movies method and assert the return value
        movie_read = self.movie_handler.search(
            f"{movie2.title} {movie2.imdb_id} {movie2.tmdb_id} {movie2.year}"
        )
        assert len(movie_read) == 1
        assert movie_read[0].connection_id == movie2.connection_id
        assert movie_read[0].radarr_id == movie2.radarr_id
        assert movie_read[0].title == movie2.title
        assert movie_read[0].year == movie2.year
        assert movie_read[0].imdb_id == movie2.imdb_id
        assert movie_read[0].tmdb_id == movie2.tmdb_id
        assert movie_read[0].monitor is False

    def test_search_tmdb_id_success(self):
        # Create a movie to read
        movie2 = MovieCreate(
            connection_id=1,
            radarr_id=208,
            title="Movie Title 200",
            imdb_id="tt12345690",
            tmdb_id="123458",
            year=2022,
        )
        assert self.movie_handler.create(movie2) is True

        # Call the search_movies method and assert the return value
        movie_read = self.movie_handler.search(
            f"{movie2.title} {movie2.tmdb_id} {movie2.year}"
        )
        assert len(movie_read) == 1
        assert movie_read[0].connection_id == movie2.connection_id
        assert movie_read[0].radarr_id == movie2.radarr_id
        assert movie_read[0].title == movie2.title
        assert movie_read[0].year == movie2.year
        assert movie_read[0].imdb_id == movie2.imdb_id
        assert movie_read[0].tmdb_id == movie2.tmdb_id
        assert movie_read[0].monitor is False

    def test_search_year_success(self):
        # Create a movie to read
        movie2 = MovieCreate(
            connection_id=1,
            radarr_id=209,
            title="Movie Title 200",
            imdb_id="tt12345691",
            tmdb_id="123459",
            year=2022,
        )
        assert self.movie_handler.create(movie2) is True

        # Call the search_movies method and assert the return value
        movie_read = self.movie_handler.search(f"{movie2.title} {movie2.year}")
        assert len(movie_read) >= 1
        assert movie_read[0].year == movie2.year

    def test_search_fail_no_query(self):
        # Call the search_movies method and assert the return value
        movie_read = self.movie_handler.search("")
        assert len(movie_read) == 0

    def test_search_fail_no_results(self):
        # Create a movie to read
        movie2 = MovieCreate(connection_id=1, radarr_id=220, title="Movie Title 200")
        assert self.movie_handler.create(movie2) is True

        # Call the search_movies method and assert the return value
        movie_read = self.movie_handler.search("No Results Invalid Movie")
        assert len(movie_read) == 0

    def test_update_success(self):
        # Create a movie to update
        assert self.movie_handler.create_or_update_bulk([movie]) is True

        # Call the update_movie method and assert the return value
        assert self.movie_handler.update(MOVIE_ID_1, movie_update) is True

        # Call the read_movie method and assert the return value
        movie_read = self.movie_handler.read(MOVIE_ID_1)
        assert movie_read is not None
        assert movie_read.connection_id == movie.connection_id
        assert movie_read.radarr_id == movie.radarr_id
        assert movie_read.title == movie.title
        assert movie_read.year == movie.year
        assert movie_read.imdb_id == movie.imdb_id
        assert movie_read.tmdb_id == movie.tmdb_id
        assert movie_read.monitor is True
        assert movie_read.radarr_monitored is True

    def test_update_failed(self):
        # Call the update_movie method and assert the return value
        with pytest.raises(Exception) as exc_info:
            self.movie_handler.update(2050, movie_update)
        assert exc_info.type.__name__ == "ItemNotFoundError"
        assert str(exc_info.value) == NO_MOVIE_MESSAGE.format(2050)

    def test_delete_success(self):
        # Create a movie to delete
        assert self.movie_handler.create_or_update_bulk([movie]) is True

        # Call the delete_movie method and assert the return value
        assert self.movie_handler.delete(MOVIE_ID_1) is True

        # Call the read_movie method and assert an ItemNotFoundError is raised
        with pytest.raises(Exception) as exc_info:
            self.movie_handler.read(MOVIE_ID_1)
        assert exc_info.type.__name__ == "ItemNotFoundError"
        assert str(exc_info.value) == NO_MOVIE_MESSAGE.format(MOVIE_ID_1)

    def test_delete_failed(self):
        # Call the delete_movie method and assert the return value
        with pytest.raises(Exception) as exc_info:
            self.movie_handler.delete(2050)
        assert exc_info.type.__name__ == "ItemNotFoundError"
        assert str(exc_info.value) == NO_MOVIE_MESSAGE.format(2050)

    def test_delete_bulk_success(self):
        # Create some movies to delete
        movie2 = MovieCreate(connection_id=1, radarr_id=221, title="Movie Title 200")
        assert self.movie_handler.create(movie2) is True
        movie3 = MovieCreate(connection_id=1, radarr_id=222, title="Movie Title 200")
        assert self.movie_handler.create(movie3) is True

        # Call the delete_all_movies method and assert the return value
        assert self.movie_handler.delete_bulk(set([2, 3])) is True

        # Call the read_movie method and assert an ItemNotFoundError is raised
        with pytest.raises(Exception) as exc_info:
            self.movie_handler.read(MOVIE_ID_1)
        assert exc_info.type.__name__ == "ItemNotFoundError"
        assert str(exc_info.value) == NO_MOVIE_MESSAGE.format(MOVIE_ID_1)

    def test_delete_bulk_failed(self):
        # Call the delete_all_movies method and assert the return value
        with pytest.raises(Exception) as exc_info:
            self.movie_handler.delete_bulk(set([1000]))
        assert exc_info.type.__name__ == "ItemNotFoundError"
        assert str(exc_info.value) == NO_MOVIE_MESSAGE.format(1000)