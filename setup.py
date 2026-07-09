from setuptools import setup, find_packages

setup(
    name="neplatic-desktop",
    version="2.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "psycopg2-binary>=2.9.0",
        "SQLAlchemy>=2.0.0",
        "geoalchemy2>=0.14.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "folium>=0.15.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "bcrypt>=4.0.0",
        "PyJWT>=2.8.0",
    ],
    python_requires=">=3.10",
)