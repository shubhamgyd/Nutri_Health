import os
from flask import Flask, render_template, request, flash
import pickle
import numpy as np
from PIL import Image
import tensorflow as tf
from ocr import preprocess_image, extract_text_from_image, extract_medical_fields

app = Flask(__name__)
#app.secret_key = 'your_secret_key_here'  # Required for flash messages

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the uploads directory exists
app.secret_key = 'your_secret_key_here'  # Required for flash messages

def predictDiabetes(input_data):
    # input_data = (5,166,72,19,175,25.8,0.587,51)
    # filename = 'diabetes_model.sav'
    # pickle.dump(classifier, open(filename, 'wb'))
    loaded_model = pickle.load(open('./models/diabetes_model.sav', 'rb'))

    # changing the input_data to numpy array
    input_data_as_numpy_array = np.asarray(input_data)

    # reshape the array as we are predicting for one instance
    input_data_reshaped = input_data_as_numpy_array.reshape(1,-1)

    prediction = loaded_model.predict(input_data_reshaped)
    print(prediction)
    return prediction

def predict(values, dic):
    # diabetes
    if len(values) == 8:
        dic2 = {'NewBMI_Obesity 1': 0, 'NewBMI_Obesity 2': 0, 'NewBMI_Obesity 3': 0, 'NewBMI_Overweight': 0,
                'NewBMI_Underweight': 0, 'NewInsulinScore_Normal': 0, 'NewGlucose_Low': 0,
                'NewGlucose_Normal': 0, 'NewGlucose_Overweight': 0, 'NewGlucose_Secret': 0}

        if dic['BMI'] <= 18.5:
            dic2['NewBMI_Underweight'] = 1
        elif 18.5 < dic['BMI'] <= 24.9:
            pass
        elif 24.9 < dic['BMI'] <= 29.9:
            dic2['NewBMI_Overweight'] = 1
        elif 29.9 < dic['BMI'] <= 34.9:
            dic2['NewBMI_Obesity 1'] = 1
        elif 34.9 < dic['BMI'] <= 39.9:
            dic2['NewBMI_Obesity 2'] = 1
        elif dic['BMI'] > 39.9:
            dic2['NewBMI_Obesity 3'] = 1

        if 16 <= dic['Insulin'] <= 166:
            dic2['NewInsulinScore_Normal'] = 1

        if dic['Glucose'] <= 70:
            dic2['NewGlucose_Low'] = 1
        elif 70 < dic['Glucose'] <= 99:
            dic2['NewGlucose_Normal'] = 1
        elif 99 < dic['Glucose'] <= 126:
            dic2['NewGlucose_Overweight'] = 1
        elif dic['Glucose'] > 126:
            dic2['NewGlucose_Secret'] = 1

        dic.update(dic2)

        # values2 = list(map(float, list(dic.values())))
        values2 = {'names': [], 'formats': []}
        for key in dic:
            values2["names"].append(key)
            values2["formats"].append(dic[key])

        model = pickle.load(open('models/diabetes.pkl','rb'))
        # values = np.asarray(values2)
        values = values2

        return model.predict(values.reshape(1, -1))[0]


    # breast_cancer
    elif len(values) == 22:
        model = pickle.load(open('models/breast_cancer.pkl','rb'))
        values = np.asarray(values)
        return model.predict(values.reshape(1, -1))[0]

    # heart disease
    elif len(values) == 13:
        model = pickle.load(open('models/heart.pkl','rb'))
        values = np.asarray(values)
        return model.predict(values.reshape(1, -1))[0]

    # kidney disease
    elif len(values) == 24:
        model = pickle.load(open('models/kidney.pkl','rb'))
        values = np.asarray(values)
        return model.predict(values.reshape(1, -1))[0]

    # liver disease
    elif len(values) == 10:
        model = pickle.load(open('models/liver.pkl','rb'))
        values = np.asarray(values)
        return model.predict(values.reshape(1, -1))[0]

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/diabetes", methods=['GET', 'POST'])
def diabetesPage():
    return render_template('diabetes.html')

@app.route("/cancer", methods=['GET', 'POST'])
def cancerPage():
    return render_template('breast_cancer.html')

@app.route("/heart", methods=['GET', 'POST'])
def heartPage():
    return render_template('heart.html')

@app.route("/kidney", methods=['GET', 'POST'])
def kidneyPage():
    return render_template('kidney.html')

@app.route("/liver", methods=['GET', 'POST'])
def liverPage():
    data = None
    if request.method == 'POST':
        if 'image_file' in request.files:
            image_file = request.files['image_file']
            if image_file:
                # Save the uploaded image
                image_path = os.path.join('uploads', image_file.filename)
                image_file.save(image_path)

                # Use OCR functions from ocr.py to extract data
                preprocessed_image = preprocess_image(image_path)
                if preprocessed_image is not None:
                    extracted_text = extract_text_from_image(preprocessed_image)
                    if extracted_text:
                        data = extract_medical_fields(extracted_text)
                        
                        # Handle Gender field (not present in OCR output)
                        data['Gender'] = ''
                        
                        # Check if any fields are "Not found"
                        not_found_fields = [field for field, value in data.items() if value == "Not found"]
                        if not_found_fields:
                            flash(f"Some fields could not be extracted: {', '.join(not_found_fields)}. Please fill them manually.", "warning")
                        else:
                            flash("Data successfully extracted from the image. Please review and correct if necessary.", "success")
                    else:
                        flash("Could not extract text from the image. Please enter the data manually.", "error")
                else:
                    flash("Could not process the image. Please try again with a clearer image.", "error")
                
                # Clean up the uploaded file
                os.remove(image_path)
            else:
                flash("No file uploaded. Please select an image file.", "error")

    return render_template('liver.html', data=data)

@app.route("/malaria", methods=['GET', 'POST'])
def malariaPage():
    return render_template('malaria.html')

@app.route("/pneumonia", methods=['GET', 'POST'])
def pneumoniaPage():
    return render_template('pneumonia.html')

@app.route("/predict", methods = ['POST', 'GET'])
def predictPage():
    print()
    try:
        if request.method == 'POST':
            data = request.form.to_dict()
            # to_predict_dict = {'Pregnancies': '6', 'Glucose': '148', 'BloodPressure': '72', 'SkinThickness': '35', 'Insulin': '0', 'BMI': '33.6', 'DiabetesPedigreeFunction': '0.627', 'Age': '50'}
            # print(to_predict_dict)

            # for key, value in to_predict_dict.items():
            #     try:
            #         to_predict_dict[key] = int(value)
            #     except :
            #         to_predict_dict[key] = float(value)
            # to_predict_list = list(map(float, list(to_predict_dict.values())))
            # pred = predict(to_predict_list, to_predict_dict)

            # data = {'Pregnancies': '6', 'Glucose': '148', 'BloodPressure': '72', 'SkinThickness': '35', 'Insulin': '0', 'BMI': '33.6', 'DiabetesPedigreeFunction': '0.627', 'Age': '50'}

            # Convert values to appropriate types (int/float)
            values_tuple = tuple(
                float(value) if '.' in value else int(value) 
                for value in data.values()
            )
            print(values_tuple)


            pred = predictDiabetes(values_tuple)
    except Exception as e:
        print(e)
        message = "Please enter valid data"
        return render_template("home.html", message=message)

    return render_template('predict.html', pred=pred)

@app.route("/malariapredict", methods = ['POST', 'GET'])
def malariapredictPage():
    if request.method == 'POST':
        try:
            img = Image.open(request.files['image'])
            img.save("uploads/image.jpg")
            img_path = os.path.join(os.path.dirname(__file__), 'uploads/image.jpg')
            os.path.isfile(img_path)
            img = tf.keras.utils.load_img(img_path, target_size=(128, 128))
            img = tf.keras.utils.img_to_array(img)
            img = np.expand_dims(img, axis=0)

            model = tf.keras.models.load_model("models/malaria.h5")
            pred = np.argmax(model.predict(img))
        except:
            message = "Please upload an image"
            return render_template('malaria.html', message=message)
    return render_template('malaria_predict.html', pred=pred)

@app.route("/pneumoniapredict", methods = ['POST', 'GET'])
def pneumoniapredictPage():
    if request.method == 'POST':
        try:
            img = Image.open(request.files['image']).convert('L')
            img.save("uploads/image.jpg")
            img_path = os.path.join(os.path.dirname(__file__), 'uploads/image.jpg')
            os.path.isfile(img_path)
            img = tf.keras.utils.load_img(img_path, target_size=(128, 128))
            img = tf.keras.utils.img_to_array(img)
            img = np.expand_dims(img, axis=0)

            model = tf.keras.models.load_model("models/pneumonia.h5")
            pred = np.argmax(model.predict(img))
        except:
            message = "Please upload an image"
            return render_template('pneumonia.html', message=message)
    return render_template('pneumonia_predict.html', pred=pred)

if __name__ == '__main__':
    app.run(debug = True)