import cv2
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import pprint as pp
import numpy as np
from PIL import Image, ImageDraw
import glob
import os
import random
from scipy.ndimage.filters import gaussian_filter
from skimage.transform import AffineTransform, warp
import yaml


def addArtifactsLocal():
    with open("config.yml",'r') as ymlfile:
        cfg = yaml.safe_load(ymlfile)
    addArtifacts(cfg)

def addArtifacts(home, runName, imgMeanRange, imgStd, gaussian, doSmartNoise, smartNoisePath, smartNoise, numCircles, addGrid, gridRange, stds):
    print("Adding Artifacts")

    def randAdd(row):
        return row+random.randint(0,30)

    def addScans(img):
        xDim,yDim,zDim = img.shape
        for i in range(0,xDim):
            img[i,:,:] = img[i,:,:]+random.randint(-30,30)
        for i in range(0,yDim):
            img[:,i,:] = img[:,i,:]+random.randint(-30,30)
        
        return img

    def skewImage(image,shift):

        transform = AffineTransform(translation=shift)
        shifted = warp(image,transform, mode ='wrap', preserve_range =True)
        shifted = shifted.astype(image.dtype)
        return shifted

    def standardize(image):
        image = image.astype(np.float64)
        imgMean = np.mean(image)
        imgSTD = np.std(image)
        image= (image - imgMean)/(stds*imgSTD)
        image = image+0.5
        #image = image*255
        image = np.clip(image,0,1)
        return image


    def standardizeRand(image):
        image = image.astype(np.float64)
        imgMean = np.mean(image)
        imgSTD = np.std(image)
        image= (image - imgMean)/(random.uniform(imgStd[0], imgStd[1])*imgSTD)
        image = image+random.uniform(imgMeanRange[0], imgMeanRange[1])
        image = np.clip(image,0,1)
        return image

    def addCircle(image,xCoord,yCoord,radius):
        dims = image.shape
        xx,yy = np.mgrid[:dims[0],:dims[1]]

        radius = 10

        circle = radius>((xx - xCoord)**2+(yy-yCoord)**2)**(1/2)

        image[circle] = image[circle] + random.uniform(-0.5,0.5)
        return image

    def nRandCircles(image,n):
        dims = image.shape
        for i in range(0,n):
            image = addCircle(image,random.randint(0,dims[0]),random.randint(0,dims[1]),random.randint(5,20))
        return image


    def rgb2gray(rgb):

        r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
        gray = 0.2989 * r + 0.5870 * g + 0.1140 * b

        return gray

    def randomChanges(image):
        sigmaMin = gaussian[0]
        sigmaMax = gaussian[1]

        gDims = image.shape
        image = gaussian_filter(image,sigma=random.uniform(sigmaMin,sigmaMax))
        #image = image*random.uniform(0.4,1.6)
        if addGrid:
            image = randomGrid(image)
        image = nRandCircles(image, numCircles)
        return image

    def addSmartNoise(image,noiseImages):
        smartNoiseMin = smartNoise[0]
        smartNoiseMax = smartNoise[1]

        noiseImage = noiseImages[random.randint(0,len(noiseImages))-1]
        noiseImage = standardize(noiseImage)
        nDims = noiseImage.shape
        gDims = image.shape
        xSkew = random.randint(0,nDims[0])
        ySkew = random.randint(0,nDims[1])
        noiseImage = skewImage(noiseImage,(xSkew,ySkew))
        if nDims[0]>=gDims[0] and nDims[1]>=gDims[1]:
            noiseImage = noiseImage[0:gDims[0],0:gDims[1],:]
        else:
            noiseImage = cv2.resize(noiseImage, dsize=(gDims[0], gDims[1]), interpolation=cv2.INTER_CUBIC)
        noiseStrength = random.uniform(smartNoiseMin,smartNoiseMax)
        image = image+noiseImage*noiseStrength
        return image
        
    def randomGrid(image):
        bShift = gridRange
        dims = image.shape
        x = random.randint(0,dims[0])
        y = random.randint(0,dims[1])
        image[:x,:y] = image[:x,:y] +random.uniform(-bShift,bShift)
        image[x:,:y] = image[x:,:y] +random.uniform(-bShift,bShift)
        image[:x,y:] = image[:x,y:] +random.uniform(-bShift,bShift)
        image[:x,:y] = image[:x,:y] +random.uniform(-bShift,bShift)
        return image


    def doForAll(home, runName, imgMeanRange, imgStd, gaussian, doSmartNoise, smartNoisePath, smartNoise, numCircles, addGrid, gridRange, stds):

        targetDir = os.path.join(home, runName)

        ext = 'jpg'
        outEXT = 'jpg'
        outDir = os.path.join(targetDir,"enchanced")

        if not os.path.exists(outDir):
            os.makedirs(outDir)
        else:
            print("Enchanced simulation image directory already exists. Aborting.")
            return

        filePattern = 	os.path.join(targetDir,"*." + ext)
        num = 1
        for filename in glob.glob(filePattern):
            num = num+1
            imgcv = cv2.imread(filename)

            imName = os.path.basename(filename)

            prePost = imName.split(".")
            noEnd = prePost[0]

            imgMean = np.mean(imgcv)
            imgSTD = np.std(imgcv)

            image = standardizeRand(imgcv)

            if doSmartNoise:
                noiseImages = []
                noisePath = os.path.join(home, smartNoisePath)
                noiseFilePattern = os.path.join(noisePath,'*.jpg')

                for filename in glob.glob(noiseFilePattern):
                    imgcv = cv2.imread(filename)
                    noiseImages.append(imgcv)
                image = randomChanges(image)
                image = addSmartNoise(image,noiseImages)
            else:
                image = randomChanges(image)


            image = standardize(image)
            image = rgb2gray(image)

            image = np.clip(image,0,1)
            im = Image.fromarray(image*255)

            if im.mode != 'RGB':
                im = im.convert('RGB')
            saveName = os.path.join(outDir,noEnd+'.'+outEXT)
            im.save(saveName)

    #script start        
    doForAll(home, runName, imgMeanRange, imgStd, gaussian, doSmartNoise, smartNoisePath, smartNoise, numCircles, addGrid, gridRange, stds)

if __name__ == '__main__':
    addArtifactsLocal()