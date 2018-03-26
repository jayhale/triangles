from setuptools import setup


setup(
    name='triangles',
    version='0.0.0',
    py_modules=['triangles'],
    install_requires=['click>=6.7,<7', 'sqlalchemy>=1.2,<1.3'],
    entry_points='''
        [console_scripts]
        triangle=triangles.commands:cli
    '''
)
