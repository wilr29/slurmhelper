from setuptools import setup
import versioneer

setup(
    name='slurmhelper',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    # packages=find_namespace_packages(include=['slurmhelper.*']),
    url='https://github.com/fcmeyer/slurmhelper',
    license='MIT',
    author='Francisco Meyer',
    author_email='f.meyer@vanderbilt.edu',
    description='Helper tool for running jobs on an HPC that uses SLURM'
)
