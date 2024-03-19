# Rate Limiter

Rate Limiter is a Python reverse proxy designed to manage and enforce rate limits in applications. It provides a simple and flexible interface for controlling the rate of requests or actions within a specified time frame, leveraging header identifier of userId.

<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>


## Quick start

### Manual setup

Install all dependencies

```bash
pip install poetry
poetry install
```

Then run

```bash
uvicorn src.rate_limiter.main:app --port 8000
```

Via docker

```bash
docker compose up --build
```

## Configuration

In order to set the limits of adjust the window correct the values in **example.env** and rename it to **.env**

* **RATE_LIMITER_NUMBER_OF_TOKENS** - Number of requests allowed per amount of time 
* **RATE_LIMITER_WINDOW** - Time is seconds, after which counter will be reset
* **RATE_LIMITER_LIMIT** - The limit, which can be acheived by summing tokens from the past. If different from 0, limiter will work in accumulator mode and sum up unused requests from previous time frame.

## Features

* Support in-memory tracking request counts
* Flexible rate limit configurations
* Easy integration into the applications

## Contributing

Contributions are welcome! If you have any suggestions, bug reports, or feature requests, please open an issue or submit a pull request on GitHub.
