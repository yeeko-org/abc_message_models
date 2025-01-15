from setuptools import setup, find_packages

setup(
    name='yeeko_abc_message_models',
    version='0.1.2',
    description='models and abstract classes for creating and sending instant messages',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='vash Lucian',
    author_email='lucian@yeeko.org',
    url='https://github.com/yeeko-org/abc_message_models',
    packages=find_packages(),
    install_requires=[
        "pydantic==2.10.5",
        "requests==2.32.3"
    ],
    python_requires='>=3.6',
)
