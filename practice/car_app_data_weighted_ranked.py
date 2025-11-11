#Aleksandr Polskiy practice on sample app data
#car data: period as an array of dictionaries is parsed and printed
#Then alternatively this array of dictionaries is extracted into a pandas dataframe,
# where each dictionaryis a row and each datapoint in the dictionary is a column
#Inserting four additional columns ranking each relevant datapoint in individual
# dictionary then inserting final column which includes average
# of the sum of all ranking columns for this row (dictionary)each ranks
"""an array of dictionaries containing app data from a car for example, is parsed
into a pandas dataframe, where certain data poins are weighted and then ranked"""
import pandas as pd
import numpy as np

#function that prints key value pairs prom a nested dictionaries
def print_nested_dict(d, indent=0):
    """This function prints key value pairs from a nested dictionary"""
    for key, value in d.items():
        print(' '*indent+str(key)+':', end=' ')
        if isinstance(value, dict):
            print(" ")
            print_nested_dict(value, indent+1)
        else:
            print(value)


period = [
    {'app': 'car', 'fps_data':
        {'l_frame': 100,
         'sframe': 7,
         'fps': 56.45,
         'frames_over_25ms': 10}},
    {'app': 'phone', 'fps_data':
        {'l_frame': 20,
         'sframe': 3,
         'fps': 58.8,
         'frames_over_25ms': 0
         }},

    {'app': 'car', 'fps_data':
        {'l_frame': 40,
         'sframe': 7,
         'fps': 33.36,
         'frames_over_25ms': 9
         }},

    {'app': 'phone', 'fps_data':
        {'l_frame': 17,
         'sframe': 7,
         'fps': 62.2,
         'frames_over_25ms': 9
         }},

    {'app': 'spotify', 'fps_data':
        {'l_frame': 100,
         'sframe': 7,
         'fps': 56.45,
         'frames_over_25ms': 9
         }},

    {'app': 'car', 'fps_data':
        {'l_frame': 100,
         'sframe': 7,
         'fps': 56.45,
         'frames_over_25ms': 0
         }},

    {'app': 'maps', 'fps_data':
        {'l_frame': 50,
         'sframe': 10,
         'fps': 45.67,
         'frames_over_25ms': 10
         }},

    {'app': 'maps', 'fps_data':
        {'l_frame': 45,
         'sframe': 20,
         'fps': 65.65,
         'frames_over_25ms': 10
         }},
]

#extracting and printing particular values from period an array of dictionaries
for item in period:
    print("\n")
    print(item["app"]+":"+str(item["fps_data"]["l_frame"])+
          ":"+str(item["fps_data"]["sframe"])+":"+str(item["fps_data"]["fps"])+":"+
          str(item["fps_data"]["frames_over_25ms"]))
    print("\n")

#extracting and printing key value pairs from particular dictionary
for item in period:
    print_nested_dict(item)
    print("\n")

#extracting data from period into dataframe treating each each dictionary as a json object
df = pd.json_normalize(period)
print("\n Dataframe after being normalized as json from period array of dictionaries: \n")
print(df)

#removing the prefixes that include . for all columns, leaving only suffixes after the period
df.columns = [col.split('.')[-1] for col in df.columns]
print(df)
print("\n")

#evaluating length, fps, of frame for ranking
l_conditions = [
df['l_frame'] <= 16.67,
df['l_frame'] > 16.67
]
l_selections = [
1,
df['l_frame']//16.67+1
]

fps_conditions=[
    1000/df['fps'] >= 16.67,
    1000//df['fps'] < 16.67
]

fps_selections=[
    1,
    1000/df['fps']//16.67+1
]



#setting ranking for length of frame, jitter (number of frames with over 25ms length),
# and fps, where average length of a frame was over 16.67ms
df['max_l_ranking'] = np.select(l_conditions, l_selections, default=1)
df['jitter_ranking'] = df['frames_over_25ms']+1
df['fps_ranking'] = np.select(fps_conditions, fps_selections, default=1)
df['max_l_ranking']= df['max_l_ranking'].astype(int)
df['fps_ranking'] = df['fps_ranking'].astype(int)
#
print("\n Printing the data frame before the final column is added.\n")
print(df)

df['final_ranking']= (df['max_l_ranking']+df['jitter_ranking']+df['fps_ranking']) //3
print("\n Printing the data frame after the final column is added, but not sorted:\n")

print(df)
print("\n")
print("\n Values sorted by final_ranking")
df_final_ranking = df.sort_values(by='final_ranking')

print("\n Ranking selection of values sorted")
df_print_ranking = df_final_ranking[['app','max_l_ranking','jitter_ranking',
                                     'fps_ranking','final_ranking']]
print(df_print_ranking.to_string())
