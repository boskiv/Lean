import os
import re
import sys
import json
import subprocess
import statistics
from pathlib import Path

dataPath = sys.argv[1] if len(sys.argv) > 1 else '../../../Data'
print(f'Using data path {dataPath}')

results = {}
for baseDirectory in ["Algorithm.CSharp/Benchmarks", "Algorithm.Python/Benchmarks"]:

	language = baseDirectory[len("Algorithm") + 1:baseDirectory.index("/")]
	resultsPerLanguage = {}

	for algorithmFile in sorted(os.listdir(baseDirectory)):
		if algorithmFile.endswith(("py", "cs")):

			algorithmName = Path(algorithmFile).stem
			algorithmLocation = "QuantConnect.Algorithm.CSharp.dll" if language == "CSharp" else os.path.join("../../../", baseDirectory, algorithmFile)
			print(f'Start running algorithm {algorithmName} language {language}...')

			dataPointsPerSecond = []
			benchmarkLengths = []
			for _ in range(1, 2):
				subprocess.run(
					[
						"dotnet",
						"./QuantConnect.Lean.Launcher.dll",
						f"--data-folder {dataPath}",
						f"--algorithm-language {language}",
						f"--algorithm-type-name {algorithmName}",
						f"--algorithm-location {algorithmLocation}",
						"--log-handler ConsoleErrorLogHandler",
						"--close-automatically true",
					],
					cwd="./Launcher/bin/Release",
					stdout=subprocess.DEVNULL,
					stderr=subprocess.DEVNULL,
				)

				algorithmLogs = os.path.join(
					"./Launcher/bin/Release", f"{algorithmName}-log.txt"
				)
				file = open(algorithmLogs, 'r')
				for line in file:
					dataPointsPerSecond.extend(
						int(match)
						for match in re.findall(r"(\d+)k data points per second", line)
					)
					benchmarkLengths.extend(
						int(match) for match in re.findall(r" completed in (\d+)", line)
					)
			averageDps = statistics.mean(dataPointsPerSecond)
			averageLength = statistics.mean(benchmarkLengths)
			resultsPerLanguage[algorithmName] = { "average-dps": averageDps, "samples": dataPointsPerSecond, "average-length": averageLength }
			print(f'Performance for {algorithmName} language {language} avg dps: {averageDps}k samples: [{",".join(str(x) for x in dataPointsPerSecond)}] avg length {averageLength} sec')

	results[language] = resultsPerLanguage

with open("benchmark_results.json", "w") as outfile:
	json.dump(results, outfile)
