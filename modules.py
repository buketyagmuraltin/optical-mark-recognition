import cv2
import numpy as np
import skimage.filters
import inputs

inputImage, numberOfQuestions, numberOfChoices, partialGrade, correctAnswers = \
    inputs.inputImage, inputs.numberOfQuestions, inputs.numberOfChoices, inputs.partialGrade, inputs.correctAnswers


def rescaleFrame(frame, scale):
    """
    Rescales a frame by a given scale factor. This function resizes an input frame by multiplying its dimensions with
    a scale factor, and returns the resulting rescaled frame for further processing or display.

    :param frame: The input frame to be rescaled.
    :param scale: The scale factor to resize the frame (default is 0.5). The scale value should be a floating-point
                  number between 0 and 1. A scale factor of 1 represents the original size of the frame, while a scale
                  factor of 0.5 reduces the frame dimensions by half.
    :return: The rescaled frame.

    """

    width = int(frame.shape[1] * scale)
    height = int(frame.shape[0] * scale)
    dimensions = (width, height)

    return cv2.resize(frame, dimensions, interpolation=cv2.INTER_AREA)


def imageProcessing():
    """
    Performs image processing tasks on the original image.

    :return: A tuple containing the detected circles and the rescaled image.
             The detected circles are represented by the variable 'circles', which can be None if no circles are found.
             The rescaled image is represented by the variable 'rescaledImage'.
    """

    originalImage = cv2.imread(inputImage)
    original = rescaleFrame(originalImage, 0.5)
    rescaledImage = rescaleFrame(originalImage, 0.5)
    # cv2.imshow("Rescaled image", rescaledImage)

    gray = cv2.cvtColor(rescaledImage, cv2.COLOR_BGR2GRAY)
    # cv2.imshow("Gray", gray)

    blurred = cv2.GaussianBlur(gray, (15, 15), 0)
    # cv2.imshow("Blurred", blurred)

    # Threshold value
    t = skimage.filters.threshold_otsu(blurred) - 48
    # print("Found automatic threshold t = {}.".format(t))

    # All pixels value above t will be set to 255
    th, thresholdImage = cv2.threshold(blurred, t, 255, cv2.THRESH_BINARY_INV)
    # cv2.imshow('th', thresholdImage)

    # Detects circles using the Hough transform method
    circles = cv2.HoughCircles(thresholdImage, cv2.HOUGH_GRADIENT, 1, 20, param1=25, param2=10, minRadius=5,
                               maxRadius=20)
    print(circles)
    original = original[:, :, 0]

    # Concatenate image horizontally
    processing = np.concatenate((original, gray, blurred, thresholdImage), axis=1)
    leftWindowName = 'Image Processing (Original - Gray -  Blur - Threshold)'

    cv2.imshow(leftWindowName, rescaleFrame(processing, 0.7))
    cv2.moveWindow(leftWindowName, 20, 30)

    return circles, rescaledImage


def categorizingCircles(rescaledImage, circles):
    """
    Categorizes circles based on their coordinates on the rescaled image.

    :param rescaledImage: The rescaled image.
    :param circles: Detected circles as a NumPy array of coordinates (x, y, radius).
    :return: A tuple containing categorized options, x-y coordinates, and radii of the detected circles.
             The categorized options are represented by the variable 'markedOptions', which is a list of strings.
             The x-y coordinates are represented by the variable 'xy_values', which is a list of coordinate pairs.
             The radii of the detected circles are represented by the variable 'r_values', which is a list.
    """

    detected_circles = np.uint16(np.around(circles))
    xy_values = []
    r_values = []
    # Extract x-y coordinates and radii from the detected circles
    for pt in detected_circles[0, :]:
        a, b, r = pt[0], pt[1], pt[2]
        xy_values.append([a, b])
        r_values.append(r)

    # Sort xy_values based on y
    xy_values.sort(key=lambda x: x[1])
    # Find the minimum and maximum x-coordinates
    min_x = min(xy_values, key=lambda x: x[0])[0]
    max_x = max(xy_values, key=lambda x: x[0])[0]

    # Calculate the range width between circles
    range_width = (max_x - min_x) / (numberOfChoices - 1)
    # print('range:', range_width)
    error = range_width / 4

    # Alphabet for categorization
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    # Dict to store categorized circles
    markedOptions = []

    # Height of the rescaled image
    height = rescaledImage.shape[0]
    # Height increment for each question
    plus = height / numberOfQuestions
    # Lower bound of y coordinate for the question.
    start = 0
    # Upper bound of y coordinate for the question.
    newStart = plus
    # print(xy_values)
    numberOfMark = 0
    numberOfQuestion = 0
    print(xy_values)
    print(len(xy_values))

    while(len(xy_values )< 20):
        xy_values.append([0,0])

    # Iterates over the height of the rescaled image to categorize circles
    while start < height:
        # Categorizes the circle if its y-coordinate falls within the current question range
        if newStart > xy_values[numberOfMark][1] > start:
            x = xy_values[numberOfMark][0]
            category_id = int((x - min_x + error) / range_width)
            category = alphabet[category_id]
            markedOptions.append(category)
            newStart += plus
            start += plus
            numberOfMark += 1
            numberOfQuestion += 1
        # Adds a subcategory to the current question if the circle's y-coordinate falls
        # within the previous question range
        elif newStart - plus > xy_values[numberOfMark][1] > start - plus:
            x = xy_values[numberOfMark][0]
            category_id = int((x - min_x + error) / range_width)
            category = alphabet[category_id]
            markedOptions[numberOfQuestion - 1] += category
            numberOfMark += 1
            # If no circle is detected in the current question range, adds it as empty to the list.
        else:
            markedOptions.append("")
            # print("unmarked")
            newStart += plus
            start += plus
            numberOfQuestion += 1




    return markedOptions, xy_values, r_values


def evaluation(rescaledImage, markedOptions, xy_values, r_values):
    """
    Evaluate the marked options and provide assessment results.

    :param rescaledImage: The rescaled image.
    :param markedOptions: Categorized marked options as a list of strings.
    :param xy_values: X-Y coordinates as a list of coordinate pairs.
    :param r_values: Radii of the detected circles as a list.
    :return: A tuple containing the following assessment results:
             The modified rescaled image with circles drawn on it (represented by the variable 'rescaledImage').
             The number of correct answers (represented by the variable 'numberOfCorrectAnswers').
             The number of wrong answers (represented by the variable 'numberOfWrongAnswers').
             The number of unmarked options (represented by the variable 'numberOfUnmarkedOptions').
             The question check outputs, which provide assessment results for each question (represented by the
             variable 'questionCheckOutput').
    """

    numberOfCorrectAnswers = 0
    numberOfWrongAnswers = 0
    numberOfUnmarkedOptions = 0

    questionCheckOutput = []
    # c is the number of the marked option. It is not the same as i. Because there may be questions
    # left blank or marked 2 options.
    c = 0

    # i is the number of the current question.
    for i in range(0, numberOfQuestions):
        questionCheckOutput.append(str(i + 1) + ". Question is ")

        # There is 1 marked option 1 correct answer.
        if len(correctAnswers[i]) == 1 and len(markedOptions[i]) == 1:
            # If the marked option is the correct answer.
            if markedOptions[i] == correctAnswers[i]:
                numberOfCorrectAnswers += 1
                cv2.circle(rescaledImage, (xy_values[c][0], xy_values[c][1]), r_values[c], (0, 255, 0), 2)
                questionCheckOutput[i] += "True"
            # If the marked option is the wrong answer.
            else:
                numberOfWrongAnswers += 1
                cv2.circle(rescaledImage, (xy_values[c][0], xy_values[c][1]), r_values[c], (0, 0, 255), 2)
                questionCheckOutput[i] += "False"
            c += 1

        # There is 2 marked options and 1 correct answer.
        elif len(correctAnswers[i]) == 1 and len(markedOptions[i]) == 2:
            numberOfWrongAnswers += 1
            cv2.circle(rescaledImage, (xy_values[c][0], xy_values[c][1]), r_values[c], (0, 0, 255), 2)
            cv2.circle(rescaledImage, (xy_values[c + 1][0], xy_values[c + 1][1]), r_values[c + 1], (0, 0, 255), 2)
            questionCheckOutput[i] += "False"
            c += 2

        # There is 1 marked option and 2 correct answers.
        elif len(correctAnswers[i]) == 2 and len(markedOptions[i]) == 1:
            # If the marked option is one of the correct answers.
            if correctAnswers[i][0] == markedOptions[i] and partialGrade:
                numberOfCorrectAnswers += 0.5
                numberOfUnmarkedOptions += 0.5
                cv2.circle(rescaledImage, (xy_values[c][0], xy_values[c][1]), r_values[c], (0, 255, 255), 2)
                questionCheckOutput[i] += "Partial Grade"
            # If the marked option is one of the correct answers.
            elif correctAnswers[i][1] == markedOptions[i] and partialGrade:
                numberOfCorrectAnswers += 0.5
                numberOfUnmarkedOptions += 0.5
                cv2.circle(rescaledImage, (xy_values[c][0], xy_values[c][1]), r_values[c], (0, 255, 255), 2)
                questionCheckOutput[i] += "Partial Grade"
            # If the marked option is the wrong answer.
            else:
                numberOfWrongAnswers += 1
                cv2.circle(rescaledImage, (xy_values[c][0], xy_values[c][1]), r_values[c], (0, 0, 255), 2)
                questionCheckOutput[i] += "False"
            c += 1

        # There is 2 marked options and 2 correct answers.
        elif len(correctAnswers[i]) == 2 and len(markedOptions[i]) == 2:
            # If the marked option is the correct answer.
            if sorted(markedOptions[i]) == sorted(correctAnswers[i]):
                numberOfCorrectAnswers += 1
                cv2.circle(rescaledImage, (xy_values[c][0], xy_values[c][1]), r_values[c], (0, 255, 0), 2)
                cv2.circle(rescaledImage, (xy_values[c + 1][0], xy_values[c + 1][1]), r_values[c + 1], (0, 255, 0), 2)
                questionCheckOutput[i] += "True"
            # If the marked option is the wrong answer.
            else:
                numberOfWrongAnswers += 1
                cv2.circle(rescaledImage, (xy_values[c][0], xy_values[c][1]), r_values[c], (0, 0, 255), 2)
                cv2.circle(rescaledImage, (xy_values[c + 1][0], xy_values[c + 1][1]), r_values[c + 1], (0, 0, 255), 2)
                questionCheckOutput[i] += "False"
            c += 2

        # There is more than 2 marked options.
        elif len(markedOptions[i]) > 2:
            numberOfWrongAnswers += 1
            a = 0
            while a < len(markedOptions[i]):
                cv2.circle(rescaledImage, (xy_values[c + a][0], xy_values[c + a][1]), r_values[c + a], (0, 0, 255), 2)
                a += 1
            questionCheckOutput[i] += "False"
            c += len(markedOptions[i])

        # There is no marked options.
        elif len(markedOptions[i]) == 0:
            numberOfUnmarkedOptions += 1
            questionCheckOutput[i] += "Unmarked"
            c += 0

    return rescaledImage, numberOfCorrectAnswers, numberOfWrongAnswers, numberOfUnmarkedOptions, questionCheckOutput


def showOutput(rescaledImage, numberOfCorrectAnswers, numberOfWrongAnswers, numberOfUnmarkedOptions):
    """
    Displays the output image and assessment results.

    :param rescaledImage: The rescaled image.
    :param numberOfCorrectAnswers: The number of correct answers.
    :param numberOfWrongAnswers: The number of wrong answers.
    :param numberOfUnmarkedOptions: The number of unmarked options.
    """

    font = cv2.FONT_HERSHEY_SIMPLEX
    fontScale = 0.8
    color = (255, 0, 0)
    thickness = 2

    blankImage = np.ones((200, 500, 3), dtype=np.uint8)
    blankImage = 255 * blankImage

    text = "Number of correct answers= " + str(numberOfCorrectAnswers) + "\nNumber of wrong answers = " + str(
        numberOfWrongAnswers) + "\nNumber of unmarked answers = " + str(
        numberOfUnmarkedOptions) + "\nGrade: " + str(round((numberOfCorrectAnswers / numberOfQuestions * 100), 2))

    y0, dy = 40, 45
    for i, line in enumerate(text.split('\n')):
        y = y0 + i * dy
        cv2.putText(blankImage, line, (25, y), font, fontScale, color, thickness)

    # print("Number of correct answers = ", numberOfCorrectAnswers)
    # print("Number of wrong answers = ", numberOfWrongAnswers)
    # print("Number of unmarked answers = ", numberOfUnmarkedOptions)

    # Deleting unnecessary dimension to be able to use with concatenate function
    middleWindowName = "Image"
    rightWindowName = "Grade"

    cv2.imshow(middleWindowName, rescaleFrame(rescaledImage, 0.7))
    cv2.moveWindow(middleWindowName, 800, 30)

    cv2.imshow(rightWindowName, rescaleFrame(blankImage,  0.7))
    cv2.moveWindow(rightWindowName, 1100, 30)


def printOutputs(markedOptions, questionCheckOutput):
    """
    Prints the correct answers, detected options, and question check results.

    :param markedOptions: The detected options as a list.
    :param questionCheckOutput: The question check results as a list.
    """

    print("Correct Answers (User Input): ", correctAnswers)
    print("Detected Options (From Optic) : ", markedOptions)
    print("\nChecking questions (True or False or Partial grade or Unmarked) : ")
    for i in questionCheckOutput:
        print(i)