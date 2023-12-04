# aivtb

## Prerequisite
- nodejs
- python (there are bugs in 3.11, currently using 3.10)

## Components
- `admin/`: Web UI written in svelte.
- `server/`: Core functionalities and fastapi server. Api endpoints for `admin` and `subtitle`.
- `subtitle/`: Displays subtitle.
- `data/`: Finetuning data for gpt model.

## Usage
### Run admin UI
```
cd admin
yarn # install dependencies
yarn dev
```
### Run server
Fill the fields in `server/.env.sample`, and remove the `.sample` suffix.
```
cd server
python -m pip install -r requirements.txt
python -m uvicorn server:app
```
### Check audio device IDs
```
python server/audio.py
```
### Run subtitle display
```
cd subtitle
yarn # install dependencies
yarn dev
```
