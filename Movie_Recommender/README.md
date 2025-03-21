# Movie Recommendation Service

## Setup

1. Clone this repo!
```bash
git clone https://github.com/cmu-seai/group-project-s25-50-shades-of-gradient-descent.git
```

2. Move to the corresponding directory
```bash
cd group-project-s25-50-shades-of-gradient-descent
```

3. Create a virtual environment (make sure you're using python version 3.12)
```bash
python -m venv myenv
```

4. Activate your virtual environment

```bash
myenv\Scripts\activate # for windows
```
```bash
source myenv/bin/activate # for macOS/Linux
```

5. Install requirements
```bash
pip install -r requirements.txt
```

6. Environment file

We have provided a sample `.env` file. `.env.example`. Please create your `.env` file in the same manner.
```bash
KAFKA_BROKER=KAFKA_BROKER # replace with kafka broker "example: localhost:<port>"
KAFKA_BROKER=KAFKA_BROKER # replace with topic name
KAFKA_TOPIC=KAFKA_TOPIC # replace with group id
KAFKA_GROUP_ID=KAFKA_GROUP_ID # replace with actual database name
DB_NAME=DB_NAME # replace with actual database name
DB_USER=DB_USER # replace with actual database user
DB_PASSWORD=DB_PASSWORD # replace with actual database password
DB_HOST=DB_HOST # replace with actual database host
```

## Running the pipeline

### There are two ways to do this
1. If you want to directly test to get recommendations for particular users without hyperparameter tuning, you should follow the steps to use the pre-existing model.
2. If you want to test out our pipeline starting with loading the data and training the model, you should follow the steps to train a new model. NOTE: This process takes a lot of time

### Use pre-existing model
To use a pre-existing model to get recommendations, enter the following command on your terminal:
```bash
python3 app.py
```
1. The server will be up at: http://10.0.0.142:5000/
2. Enter User ID
3. Get recommendations

### Train a new model
To train a new model using the complete dataset, spanning from the initial log entry to the most recent records, enter the following command on your terminal. This will run the pipeline to build the new model. (Pipeline includes, loading all data logged yet, temporally splitting this data into train/test/validation sets, utilizes training and validation to get best parameters, utilizes the best parameters to train the final model, and saves this model to be used on the front end)
```bash
python3 main.py
```
1. Once you finish the run, your new model will be saved in `models/cf_model.pkl`
2. To get recommendations using this model run the following command on your terminal:
```bash
python3 app.py
```
3. The server will be up at: http://10.0.0.142:5000/
4. Enter User ID
5. Get recommendations

## Getting Online Analytics
To reproduce the results of the production data snapshot utilized by our team:
1. Place the csv file that has the production data used (the link to this is provided in the report) in the same location as `app.py`
2. Start `app.py` by running `python3 app.py`
3. The server showing the online analytics will be shown at: http://10.0.0.142:5000/analytics
4. You can vary the time periods of the data logged to see how the data changes.

To see this working in real time, with data logged manually:
1. Get multiple user IDs
2. Generate their recommendations
3. Rate the recommendations in real time manually
4. The real time data gets logged and you can view the analytics in the same link as above.
5. This is to show that we have the service working in real time.

#### NOTE: Only Average Ratings and Ratings Distribution are correctly represented, the other metrics are a work in progress.

## Last steps
1. Close the server
2. Deactivate your virtual environment using `deactivate`
