from setuptools import setup, find_packages

setup(
    name='analog_gauge_reader',
    version='0.1',
    packages=find_packages(),
    python_requires='>=3.8,<3.9',
    install_requires=[
        'pytorch==2.0.0',
        'torchvision==0.15.0',
        'torchaudio==2.0.0',
        'openmim==0.3.9',
        'mmengine==0.7.2',
        'mmcv==2.0.0',
        'mmdet==3.0.0',
        'mmocr==1.0.0',
        'ultralytics==8.3.184',
        'ultralytics-thop==2.0.16',
        'scikit-learn==1.3.2',
        'scikit-image==0.21.0',
        'opencv-python',
        'Pillow',
        'numpy'
    ],
    include_package_data=True,
    zip_safe=False,
)
