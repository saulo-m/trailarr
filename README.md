<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/nandyalu/trailarr/main/assets/images/trailarr-full-512-lg.png">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/nandyalu/trailarr/main/assets/images/trailarr-full-light-512-lg.png">
    <img alt="Trailarr logo with name" src="https://raw.githubusercontent.com/nandyalu/trailarr/main/assets/images/trailarr-full-primary-512-lg.png" width=50%>
  </picture>
</p>

# Trailarr

[![Python](https://img.shields.io/badge/python-3.12-3670A0?style=flat&logo=python)](https://www.python.org/) 
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) 
[![FastAPI](https://img.shields.io/badge/FastAPI-0.112.0-009688.svg?style=flat&logo=FastAPI)](https://fastapi.tiangolo.com) 
[![Angular](https://img.shields.io/badge/angular-17.3.6-%23DD0031.svg?style=flat&logo=angular)](https://angular.dev/) 
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://github.com/nandyalu/trailarr)

[![Open in Dev Containers](https://img.shields.io/static/v1?label=Dev%20Container&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/nandyalu/trailarr) 
[![Docker Build](https://github.com/nandyalu/trailarr/actions/workflows/docker-build.yml/badge.svg)](https://github.com/nandyalu/trailarr/actions/workflows/docker-build.yml) 
[![Docker Pulls](https://badgen.net/docker/pulls/nandyalu/trailarr?icon=docker&label=pulls)](https://hub.docker.com/r/nandyalu/trailarr/) 
[![GitHub Issues](https://img.shields.io/github/issues/nandyalu/trailarr?logo=github&link=https%3A%2F%2Fgithub.com%2Fnandyalu%2Ftrailarr%2Fissues)](https://github.com/nandyalu/trailarr/issues) 
[![GitHub last commit](https://img.shields.io/github/last-commit/nandyalu/trailarr?logo=github&link=https%3A%2F%2Fgithub.com%2Fnandyalu%2Ftrailarr%2Fissues)](https://github.com/nandyalu/trailarr/commits/)


Trailarr is a Docker application to download and manage trailers for your media library. It integrates with your existing services, such as [Plex](https://www.plex.tv/), [Radarr](https://radarr.video/), and [Sonarr](https://sonarr.tv/)!

Links: [Github](https://github.com/nandyalu/trailarr/) [Docker Hub](https://hub.docker.com/r/nandyalu/trailarr/)

## Features

- Manages multiple Radarr and Sonarr instances to find media
- Runs in background like Radarr/Sonarr.
- Checks if a trailer already exists for movie/series. Download it if set to monitor.
- Downloads trailer and organizes it in the media folder.
- Follows plex naming conventions.
- Downloads trailers for trailer id's set in Radarr/Sonarr.
- Searches for a trailer if not set in Radarr/Sonarr.
- Option to download desired video as trailer for any movie/series.
- Converts audio, video and subtitles to desired formats.
- Option to remove SponsorBlocks from videos (if any data is available).
- Beautiful and responsive UI to manage trailers and view details of movies and series.
- Built with Angular and FastAPI.

## Installation

### Environment Variables & Volume Mapping

Environment variables are optional.
- `TZ` - Set the timezone for the application. Default is `America/New_York`.
- `PUID` - Set the user ID for the application. Default is `1000`.
- `PGID` - Set the group ID for the application. Default is `1000`.
- `APP_DATA_DIR` - Set the application data directory. Default is `/data`. If setting this, make sure to map the volume to the same directory.

> Note: If you are setting the `APP_DATA_DIR` environment variable, make sure to set an absolute path like `/data` or `/config/abc`, and map the volume to the same directory.


Volume mapping is required.
- Change `<LOCAL_APPDATA_FOLDER>` to the folder where you want to store the application data.
- Change `<LOCAL_MEDIA_FOLDER>` to the folder where your media is stored.
- Change `<RADARR_ROOT_FOLDER>` to the folder where Radarr stores movies.
- Change `<SONARR_ROOT_FOLDER>` to the folder where Sonarr stores TV shows.
- Repeat the volume mapping for each Radarr and Sonarr instance you want to monitor.

For example, if you want to store the application data in `/var/appdata/trailarr`, local folder `/mnt/disk1/media/movies` is mapped in Radarr as `/media/movies`, and local folder `/mnt/disk1/media/tv` is mapped in Sonarr as `/media/tv`, the volume mapping would look like this:
```yaml
    volumes:
        - /var/appdata/trailarr:/data
        - /mnt/disk1/media/movies:/media/movies
        - /mnt/disk1/media/tv:/media/tv \
```

Or you could simply map local folder `/mnt/disk1/media` to `/media` in Trailarr:
```yaml
    volumes:
        - /var/appdata/trailarr:/data
        - /mnt/disk1/media:/media
```

> Note: 
> 1._Make sure the folder paths are correct and the application has read/write access to the folders._
> 2._If you have both Radarr and Sonarr with different root folders mapped to the same folder inside their containers, you would have to use multiple instances of Trailarr to work!_

### Docker Compose

To run the application, you need to have [Docker](https://docs.docker.com/get-docker/) installed on your system.

```docker
version: '3.2'
services:
    trailarr:
        image: nandyalu/trailarr:latest
        container_name: trailarr
        environment:
            - TZ=America/New_York
            - PUID=1000
            - PGID=1000
        ports:
            - 7889:7889
        volumes:
            - <LOCAL_APPDATA_FOLDER>:/data
            - <LOCAL_MEDIA_FOLDER>:<RADARR_ROOT_FOLDER>
            - <LOCAL_MEDIA_FOLDER>:<SONARR_ROOT_FOLDER>
        restart: on-failure
```


Run the following command to start the application:
```bash
docker-compose up -d
```

Open your browser and navigate to [http://localhost:7889](http://localhost:7889) to access the application.

#### Updating

To update the application, run the following commands:
```bash
docker-compose pull nandyalu/trailarr
docker-compose up -d
```

### Docker CLI

To run the application using the Docker CLI, run the following command:

```bash
docker run -d \
    --name=trailarr \
    -e TZ=America/New_York \
    -e PUID=1000 \
    -e PGID=1000 \
    -p 7889:7889 \
    -v <LOCAL_APPDATA_FOLDER>:/data \
    -v <LOCAL_MEDIA_FOLDER>:<RADARR_ROOT_FOLDER> \
    -v <LOCAL_MEDIA_FOLDER>:<SONARR_ROOT_FOLDER> \
    --restart unless-stopped \
    nandyalu/trailarr:latest
```

Open your browser and navigate to [http://localhost:7889](http://localhost:7889) to access the application.

#### Updating

To update the application, run the following commands:

Pull latest image:
```bash
docker pull nandyalu/trailarr
```

Stop and remove the existing container:
```bash
docker stop trailarr && docker rm trailarr
```

Finally, run the updated container using the same `docker run` command used during installation:
```bash
docker run -d ...
```

## Setup

1. Navigate to the application in your browser at [http://localhost:7889](http://localhost:7889).
2. Go to `Settings` > `Trailer` and adjust any settings as needed. 
3. Go to `Settings` > `Connections` and add your Radarr and Sonarr instances.
    - Click the `Add Connection` button.
    - Set the `Connection Name` to a name of your choice.
    - Set the `Type` to either `Radarr` or `Sonarr`.
    - Add the `URL` for your Radarr or Sonarr instance. 
        - For example, `http://192.168.0.15:6969`
    - Add the `API Key` from your Radarr or Sonarr instance.
        - Get `API Key` by opening Radarr/Sonarr in your browser, going to Settings > General, then copy the API key.
    - Set the `Monitor Type` to your preference. Here's what each of them does:
        - `Missing` will download trailers for movies/series without a trailer.
        - `New` will only download trailers for movies/series that gets added after the change.
        - `Sync` will download trailers for movie/series is monitored in Radarr/Sonarr.
        - `None` will not download any trailers.

        >Note 1: _You can set different monitor types for each Radarr/Sonarr instance._

        >Note 2: _If you have a huge library and don't want to download trailers for all of them, set the monitor type to `None` when adding a Radarr/Sonarr Connection. Wait for an hour or so to let the app sync all media from that connection, and change it to `New` to download trailers for new media. You can always manually set the monitor type for the movies/series you want to download trailers for._
    - Click the `Save` button to save the connection.
4. Repeat step 3 for each Radarr and Sonarr instance you want to monitor.
5. That's it! The application will now start downloading trailers for your media library.


## Support

If you need help, please craete an issue on the [GitHub repository](https://github.com/nandyalu/issues)

## Issues

Issues are very valuable to this project.

- Ideas are a valuable source of contributions others can make
- Problems show where this project is lacking
- With a question, you show where contributors can improve the user experience

Thank you for creating them.

## Contributing

Coming soon...

## License

This project is licensed under the terms of the GPL v3 license. See [GPL-3.0 license](https://github.com/nandyalu/trailarr?tab=GPL-3.0-1-ov-file) for more details.

## Disclaimer

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
