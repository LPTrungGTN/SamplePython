from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Numbers(BaseModel):
    num1: float
    num2: float


def add_numbers(num1: float, num2: float) -> float:
    return num1 + num2


def multiply_numbers(num1: float, num2: float) -> float:
    return num1 * num2


from services.calculator import add_numbers, multiply_numbers


@app.post("/add")
def add(nums: Numbers):
    result = add_numbers(nums.num1, nums.num2)
    return {"result": result}


@app.post("/multiply")
def multiply(nums: Numbers):
    result = multiply_numbers(nums.num1, nums.num2)
    return {"result": result}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
