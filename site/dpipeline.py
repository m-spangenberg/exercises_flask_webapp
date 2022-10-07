# https://pillow.readthedocs.io/en/stable/
from pathlib import Path
from random import choice
from os import scandir, remove, path
from PIL import Image, ImageOps
from shutil import make_archive, move

THUMBNAIL_SIZE = 192, 192
IMAGE_INPUT_PATH = "data/images/input/"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def data_size_user(filepath):
    '''Return cumulative size of files beneath path root'''
    pathsize = 0

    if Path(filepath).exists():
        with scandir(filepath) as folders:
            for folder in folders:
                with scandir(folder.path) as files:
                    for file in files:
                        pathsize += (Path(path.join(filepath, file.path)).stat().st_size)
            
    return str(round(pathsize / 1000000))


def data_gallery(filepath, imagecount):
    '''Return n sample of random user generated images from path'''
    # Keep track of images
    # choose random image from folder choice()
    # check for duplicates
    # do not add thumbnails
    if Path(filepath).exists():
        with scandir(filepath) as folders:
            for folder in folders:
                with scandir(folder) as folder:
                    for file in folder:
                        print(file)


def allowed_file(filename):
    '''Limit to allowed filetypes in ALLOWED_EXTENSIONS'''
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    
def upload_build(filepath):
    '''create upload folder'''
    Path(filepath).mkdir(parents=True, exist_ok=True)


def upload_purge(filepath):
    '''destroy uploaded contents'''
    if Path(filepath).exists():
        with scandir(filepath) as folder:
            for filename in folder:
                remove(filename)


def upload_scrub():
    '''scrub all uploaded files older than 1 hour from uploads folder'''
    if Path(IMAGE_INPUT_PATH).exists():
        with scandir(IMAGE_INPUT_PATH) as folders:
            for folder in folders:
                with scandir(folder) as folder:
                    for file in folder:
                        print(file)


def image_scale(file, imgW, imgH):
    '''rescale input image to respect control panel dimensions'''
    with Image.open(file) as im:
        im = ImageOps.exif_transpose(im)
        im = im.resize((imgW, imgH))
    
    return im


def image_save(file, filename, filepath):
    '''Save image to the following path'''
    file.save(path.join(filepath, filename))


def image_check(filepath):
    '''Return true if path contains images'''
    if Path(filepath).exists():
        with scandir(filepath) as folder_contents:
                for file in folder_contents:
                    if file.name:
                        return True


def image_feed(filepath):
    '''Return list of images in path'''
    contents = []
    with scandir(filepath) as folder_contents:
            for file in folder_contents:
                contents.append(file.name)

    return contents


def image_thumb_feed(filepath):
    '''Return list of thumbnails in path'''
    contents = []
    if Path(filepath).exists():
        with scandir(filepath) as folder_contents:
                for file in folder_contents:
                    if "_thumb" in str(file.name):
                        contents.append(file.name)

    return contents
                

def image_thumb(filepath):
    '''create thumnails of all images in folder'''
    if Path(filepath).exists():
        for infile in image_feed(filepath):
            img, ext = path.splitext(infile)
            with Image.open(path.join(filepath, infile)) as im:
                im.thumbnail(THUMBNAIL_SIZE)
                im.save(path.join(filepath, img + "_thumb.jpg"), "PNG")


def image_zip(filepath, rootpath, sessionid, taskid, destination):
    '''
    generate zipped archive of images 
    TODO: Fix base and root path to avoid zip errors
    move zip file from output to zip folder
    '''
    zipfile = f'{taskid}_{sessionid}'
    make_archive(path.join(filepath, zipfile), 'zip', root_dir=rootpath, base_dir=filepath)
    move(path.join(filepath, zipfile + '.zip'), path.join(destination, zipfile + '.zip'))


def archive_zip(filepath, rootpath, sessionid, taskid, destination):
    '''
    generate zipped archive of all user generated images 
    TODO: Implement user archive and data scrub
    move zip file to zip folder
    '''
    zipfile = f'{taskid}-{sessionid}'
    make_archive(path.join(filepath, zipfile), 'zip', root_dir=rootpath, base_dir='./')
    move(path.join(filepath, zipfile + '.zip'), path.join(destination, zipfile + '.zip'))