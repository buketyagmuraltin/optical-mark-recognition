import cv2
import modules

# Main code
# This code performs image processing and the evaluation of answer sheets

# Determines whether to print data as output
printOutputs = True

# Perform image processing to detect circles and obtain rescaled image
detectedCircles, rescaledImage = modules.imageProcessing()

# Check if circles are detected
if detectedCircles is not None:
    # Categorize circles and evaluate answers
    markedOptions, xy_values, r_values = modules.categorizingCircles(rescaledImage, detectedCircles)
    rescaledImage, numberOfCorrectAnswers, numberOfWrongAnswers, numberOfUnmarkedOptions, questionCheckOutput \
        = modules.evaluation(rescaledImage, markedOptions, xy_values, r_values)
else:
    # If no circles are detected, set counts accordingly
    numberOfCorrectAnswers = 0
    numberOfWrongAnswers = 0
    numberOfUnmarkedOptions = 20

# Show output image with evaluation results
modules.showOutput(rescaledImage, numberOfCorrectAnswers, numberOfWrongAnswers, numberOfUnmarkedOptions)

if printOutputs:
    modules.printOutputs(markedOptions, questionCheckOutput)

cv2.waitKey(0)
cv2.destroyAllWindows()