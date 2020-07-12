# shlabber.py - Archives a soup

Schlabbern is like auslöffeln, only much more messy

## Features
 * Works with endless scroll
 * Saves more than images
 * Preserves some metadata
 * If your soup shows timestamps, they will be used to sort the backup

## Dependencies
 * virtualenv
 * python3

To install this, run:

```sh
virtualenv venv
./venv/bin/pip install -r requirements.txt
```

## Use
Basic usage:
```
venv/bin/python3 ./schlabber <name of soup>
```
If invoked without any parameters, the programm will asume the output direcory for all files is the
working directory.
To choose an alternative output diectory supply -d \<path> to the application

For more options:
```
./schlabber -h
```
