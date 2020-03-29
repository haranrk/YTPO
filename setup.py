import setuptools
import ytpo

setuptools.setup(
    name='ytpo',
    version=ytpo.__version__,
    author="Haran Rajkumar",
    author_email="haranrajkumar97@gmail.com",
    description="YouTube Playlist Organizer",
    url="https://github.com/haranrk/",
    packages=setuptools.find_packages(),
    entry_points='''
        [console_scripts]
        ytpo=ytpo.ytpo:main
    ''',     
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],   
    
)

