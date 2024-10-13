from setuptools import setup, find_packages

setup(
    name='lime-green',
    version='0.1.0',
    description='cli-based micro-framework for llm evals',
    author='Will Sutton',
    author_email='wsutton17@gmail.com',
    packages=find_packages(),
    package_dir={'lime': 'lime'},
    package_data={
        'lime': [
            'data/*', 
            'data/datasets/*', 
            'data/datasets/simple/*', 
            'data/config_model/*'
        ],        
    },
    setup_requires=['wheel'],
    install_requires=[
        'PyYAML',
        'python-dotenv',
        'pydantic',
        'pandas',
        'tabulate',
        'openai',
        'tiktoken',
        'flask',
        'requests',
        'anthropic',
    ],
    extras_require={
        'dev': ['pytest', 'jupyter', 'llama_cpp_python'],
        'llama_cpp': ['llama_cpp_python'],
    },
    entry_points={
        'console_scripts': [
            'lime = lime.main:main'
        ]
    },
)
