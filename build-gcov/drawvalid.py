#! /usr/bin/env python3

import sys
import argparse
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from collections import defaultdict

col_names = ["not_important", "valid_packets"]

parser = argparse.ArgumentParser()

parser.add_argument("-f", "--file", action="append", required=True, help="file to read")
parser.add_argument("-n", "--name", action="append", required=True, help="Name of the data")
parser.add_argument("-o", "--output", required=True, help="Output file name")
parser.add_argument("--title", default="Valid Packets Analysis", help="Title of the plot")
parser.add_argument("--limit", type=int, default=None, help="Limit number of data points to read")

def load_data(file, limit:int|None=None):
    data = pd.read_csv(file, names=col_names, sep=' ')
    data["time_minutes"] = np.arange(len(data))
    return data[["time_minutes", "valid_packets"]].head(limit) if limit else data[["time_minutes", "valid_packets"]]

def main():
    args = parser.parse_args()
    files: list[str] = args.file 
    names: list[str] = args.name
    output: str = args.output
    
    if len(files) != len(names):
        parser.error("Number of files and names must be the same")
        
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300) 
    ax.set_title(args.title)
    ax.set_xlabel("Time (minutes)")
    ax.set_ylabel("Valid Packets")
        
    for file, name in zip(files, names):
        df = load_data(file, limit=args.limit)
        ax.plot(df["time_minutes"], df["valid_packets"], label=name)
        
    ax.legend()
    plt.savefig(output)


if __name__ == "__main__":
    main()
        