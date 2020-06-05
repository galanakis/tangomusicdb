# Tango music database

The objective of this project is to compile a database of tango music,
mostly for offline use.

## Motivations

Even though there are online databases, they require constant (and slow)
internet connection (tango.info). Some of them are only accessible with a fee (tango-dj.at)

* Create a downloadable (offline) database for easy refererence
* auto completing the data of tango audio files
* Generating tandas and playlists.

## State

This is at an early stage. I am currently generating databases by data scrapping.

## Objectives

0) Creation of an offline database
1) Local web interface
2) mp3 tagger with fuzzy matching
3) Automatic tanda generator

## Which metadata to store

Each tango performance is sufficiently described by the following fields

* Orchestra
* Title
* Singer (or instrumental)
* Recording Date (or just the year)

Additional data useful to a DJ are

* Genre
* Duration

What about the track information (album, track number or disc number)?

A bit of history on tango tunes. Each performance we know and love has been recorded and stored in some master discs. Later in the years, the same recording has been reproduced in vinyl discs, shellacs, CDs. In each reproduction it may have been subject to certain abuse such as:

* Change the speed: possibly to make the songs more upbeat, they played them faster. As a result the voices of the singers sound a bit like Mickey Mouse.
* Add sound processing: possibly to clear some of the noise. As a result some tracks may sound as if you are listening to them from the nearby building.
* Add sound effects: most notably reverberation. This is to give the impressiong that the recording occurs in a big convert hall. The result is some horrible echo which distorts all intruments.

On top of it, tracks exported from, speed altered, sound processed and reverberated CDs may also have "clicks" due to cd impurities and poor cd-ripping skills.

As a result from the original recording to the actual track there might be many layers, which are irrelevant to the performance itself. 

All that matters in the end is to find the best sounding track for the particular performance.

## Where to store the metadata

There are two main options

* In the file path
* Inside the file's metadata
* In an external file.

The advantage of filename storing is that it is a universal and perfectly portable way of storing data and maybe some music players can understand it. The disadvantage is that most players don't and therefore it will be a pain to search tracks from within a player.

The advantage of metadata storing is that it can be easily accessible by many music applications. The disadvantage is that each file format has its own tricks about metadata. Some formats, like wav, do not even have metadata. Converting audio files from one lossy format to another in order to have uniform metadata, will result in loss of quality.

Keeping metadata in an external file is what itunes does (this is the meaning the itunes library). The advantage is that it allows a uniform way of handring metadata regardless of audiofile format. The disadvange is that you need to define a strinct structure for this external file and tools to read and write from it.

The objective of this project is to deal with all forms of meta data storage.

## About iTunes ordering

Itunes, which is used by many despite its shortcomings, offers to keep the music library organized.

The format it uses is

<Sorting Album Artist>/<Sorting Album>/<DiscNo>-<TrackNo>-<Sorting Title>.<extension>

Note that it is the sorting album and and sorting album artist that define the full path of the filename.

This allows for a "hack", which allows for a reasonable sorting of the identified tango tracks.

In particular, my choice is

- Sorting Album Artist = Orchestra (D'Arienzo, Troilo, etc)
- Sorting Album = Singer (Echague, Instrumental, etc)
- Sorting Title = Recording date + Title (eg: 1943-06-02 Farolito de Papel)
- Leave the track and disc number empty.

This would create a file structure in which the top folder is the orchestra, followed by one folder per singer and then a theme labeled by recording date and title. Such a naming scheme allows for easy browsing of the songs via a file browser, even without itunes. Also it is nice to order the files by date, which defines a lot about the style of the song.

The disc and track numbers need to be left empty, because they would appear first in the name and affect the ordering.

Working on Sorting fields only, has the advantage that it does not mess with data that may be set by music fingerprinting software, such as music brainz. This scheme has the advantage that it allows for easy detection of duplicate recordings.

## Copyright

This project does not contain any actual music files or any
copyrighted material. It is built using publically accessible information.
