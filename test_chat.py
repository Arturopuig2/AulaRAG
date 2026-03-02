import requests

url = "http://127.0.0.1:8000/chat"
data = {"message": "[Contexto: asignatura actual es Mates] Cuánto es 2+2?"}
response = requests.post(url, data=data)
print("Response 1:", response.json())

data2 = {"message": "[Contexto: asignatura actual es Mates] 4"}
response2 = requests.post(url, data=data2)
print("Response 2:", response2.json())

