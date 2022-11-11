from sanic import Sanic
from sanic.response import json
from sanic.request import Request
import mysql.connector as mysqlcnr


mysqlcnn = mysqlcnr.connect(
    user="root", password='Mysql123!', database="flight_ticket_booking")
mscur = mysqlcnn.cursor(dictionary=True)

app = Sanic("flight-ticket-booking")


@app.route('/execute')
async def index(request: Request):
    mscur.execute(dict(request.get_query_args())['query'])
    return json(mscur.fetchall())

if __name__ == '__main__':
    app.run()
