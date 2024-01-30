from setuptools import setup, find_packages

setup(
    name='lime',
    version='0.1',
    description='cli tool for iterating on llm evals',
    author='Will Sutton',
    author_email='wsutton17@gmail.com',
    packages=find_packages(),
    install_requires=[
        'PyYAML',
        'python-dotenv',
        'pandas',
        'tabulate',
        'openai',
    ],
    extras_require={
        'dev': ['pytest', 'jupyter', 'llama_cpp_python'],
        'llama_cpp': ['llama_cpp_python'],
        # 'together_ai': ['together_ai_python'],
        # 'transformers': ['transformers'],
    },
    entry_points={
        'console_scripts': [
            'lime = lime.main:main'
        ]
    },
)
