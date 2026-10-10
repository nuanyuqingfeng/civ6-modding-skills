print("io|"..type(io))
if type(io)=="table" then
  print("io.open|"..type(io.open))
  print("io.write|"..type(io.write))
end
print("os.time|"..type(os and os.time))
print("debug|"..type(debug))
print("string.rep|"..type(string.rep))
-- big output test: 2000 lines
for i=1,2000 do print("BIG|"..i.."|payloadpaddingxxxxxxxxxxxxxxxxxxxxxxxxxxxx") end
print("BIGDONE")
print("---END---")
