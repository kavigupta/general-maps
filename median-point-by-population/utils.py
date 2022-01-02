import numpy as np
import pandas as pd
import wquantiles


def mean_point(frame):
    lat = (frame.INTPTLAT * frame.POP100).mean() / frame.POP100.mean()
    lon = (frame.INTPTLON * frame.POP100).mean() / frame.POP100.mean()
    return lon, lat

def median_point(frame, theta=0):
    points = np.array([frame.INTPTLON, frame.INTPTLAT])
    
    c, s = np.cos(theta), np.sin(theta)
    rot = np.array(((c, -s), (s, c)))
    
    points = rot @ points
    
    center = np.array([wquantiles.median(c, frame.POP100) for c in points])

    center = np.linalg.solve(rot, center)
    
    return tuple(center)

def load_data():
    df = pd.read_csv("/home/kavi/temp/blocks_pop_centroid.csv")
    return df[df.POP100 > 0]

def for_state(df, state):
    return df[df.STUSAB == state]