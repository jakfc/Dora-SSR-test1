print(string.format('GV1 %s', tostring(Audio.globalVolume)))
Audio.globalVolume = 0.42
print(string.format('GV2 %s', tostring(Audio.globalVolume)))
Audio.globalVolume = 1.0
print(string.format('GV3 %s', tostring(Audio.globalVolume)))
