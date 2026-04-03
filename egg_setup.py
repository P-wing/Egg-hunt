from setuptools import setup

setup(name='egg_hunt', options={
    'build_apps': {
        'gui_apps': {
            'egg_hunt':'egg_hunt.py'
        },
        
        'log_filename': '$USER_APPDATA/Egg_hunt/output.log',
        'log_append': False,
        
        'include_patterns': [
            '**/*.png',
            '**/*.bam',
            '**/*.mp3'
        ],
        
        'plugins': [
            'pandagl',
            'p3openal_audio',
            'p3ffmpeg'
        ],
    }
})