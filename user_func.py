from collections import UserList
from distutils.command.build_scripts import first_line_re
import json
import psycopg2
from flask import Flask, request, jsonify

app = Flask(__name__)

conn = psycopg2.connect ("dbname='homework' user='sarahroy' host='localhost'")
cursor = conn.cursor()

def create_all():
   cursor.execute("""
      CREATE TABLE IF NOT EXISTS Users (
         user_id SERIAL PRIMARY KEY,
         first_name VARCHAR NOT NULL,
         last_name VARCHAR,
         email VARCHAR NOT NULL UNIQUE,
         phone VARCHAR,
         city VARCHAR,
         state VARCHAR,
         org_id int,
         active smallint
      );
   """)
   cursor.execute("""
      CREATE TABLE IF NOT EXISTS Organizations (
         org_id SERIAL PRIMARY KEY,
         name VARCHAR NOT NULL,
         phone VARCHAR,
         city VARCHAR,
         state VARCHAR,
         active smallint
      );
   """)
   print("Creating tables...")
   conn.commit()


@app.route('/user/add', methods=['POST'] )
def user_add():
   post_data = request.json
   first_name = post_data.get('first_name')
   last_name = post_data.get('last_name')
   email = post_data.get('email')
   phone = post_data.get('phone')
   city = post_data.get('city')
   state = post_data.get('state')
   org_id = post_data.get('org_id')
   active = post_data.get('active')

   add_user(first_name, last_name, email, phone, city, state, org_id, active)
   
   return jsonify("User created"), 201

def add_user(first_name, last_name, email, phone, city, state, org_id, active):
   cursor.execute(f"""
   INSERT INTO Users
   (first_name, last_name, email, phone, city, state, org_id, active)
   VALUES
   (%s, %s, %s, %s, %s, %s, %s, %s);""",
   (first_name, last_name, email, phone, city, state, org_id, active))
   conn.commit()

@app.route('/user_by_id/<user_id>', methods=['GET'] )
def get_user_by_id(user_id):
      cursor.execute('SELECT * FROM users WHERE user_id=%s;', [user_id])
      results = cursor.fetchone()

      if results[7] != None:
         cursor.execute("""
            SELECT U.user_id, U.first_name, U.last_name, U.email, U.phone, U.city, U.state, U.org_id, O.name, O.phone, O.city, O.state, U.active FROM Users U JOIN Organizations O ON U.org_id=O.org_id
               WHERE U.user_id=%s;""",
               [user_id])
         results = cursor.fetchone()  
     
      print(results)
     
      if len(results) > 9:
         user = {
            'user_id': results [0],
            'first_name': results [1],
            'last_name': results [2],
            'email': results [3],
            'phone': results [4],
            'city': results [5],
            'state': results [6],
            'organization': {
               'org_id': results [7],
               'name': results [8],
               'phone': results [9],
               'city': results [10],
               'state': results [11]
            },
            'active': results [12]
         }
         return jsonify(user), 200 
      
      elif len(results) == 9:
         user = {
            'user_id': results [0],
            'first_name': results [1],
            'last_name': results [2],
            'email': results [3],
            'phone': results [4],
            'city': results [5],
            'state': results [6],
            'org_id': results [7],
            'active': results [8]
         }
         return jsonify(user), 200

      else:
         return jsonify('No User Found'), 400

@app.route('/active_users', methods=['GET'] )
def get_all_active_users():
   cursor.execute('SELECT * FROM users WHERE active=1;')
   results = cursor.fetchall()     
   
   user_list = []
     
   for users in results: 
      if users[7] != None:
         cursor.execute(f"""
         SELECT * FROM Organizations
            WHERE org_id={users[7]};""")
         org = cursor.fetchone()
      
         user = {
            'user_id': users [0],
            'first_name': users [1],
            'last_name': users [2],
            'email': users [3],
            'phone': users [4],
            'city': users [5],
            'state': users [6],
            'organization': {
               'org_id': org [0],
               'name': org [1],
               'phone': org [2],
               'city': org [3],
               'state': org [4]
            },
            'active': users [8]
         }

      else:
         user = {
            'user_id': users [0],
            'first_name': users [1],
            'last_name': users [2],
            'email': users [3],
            'phone': users [4],
            'city': users [5],
            'state': users [6],
            'org_id': users [7],
            'active': users [8]
         }

      user_list.append(user)
   
   return jsonify(user_list), 200 

@app.route('/user/activate/<user_id>', methods=['POST'] )
def user_activate(user_id):
   cursor.execute("""UPDATE users SET active=1 WHERE user_id=%s""", (user_id,))

   conn.commit()
   
   return jsonify('User Activated'), 200

@app.route('/user/deactivate/<user_id>', methods=['POST'] )
def user_deactivate(user_id):
   cursor.execute("UPDATE users SET active=0 WHERE user_id=%s", (user_id,))

   conn.commit()
   
   return jsonify('User Deactivated'), 200

@app.route('/user/delete/<user_id>', methods=['DELETE'] )
def user_delete(user_id):
   cursor.execute("""DELETE FROM Users WHERE user_id=%s""", (user_id,))

   conn.commit()
   
   return jsonify('User Deleted'), 200

@app.route('/user/update/<user_id>', methods=['POST', 'PUT'] )
def user_update(user_id):
  update_fields = []
  update_values = []
  field_names = ['first_name', 'last_name', 'email', 'phone', 'city', 'state', 'org_id', 'active']

  post_data = request.json

  for field in field_names:
    field_value = post_data.get(field)
    if field_value:
      update_fields.append(str(field) + "=%s")
      update_values.append(field_value)

  if update_fields:
    update_values.append(user_id)

    query_string = f"UPDATE users SET " + ", ".join(update_fields) + "WHERE user_id=%s"

    cursor.execute(query_string, update_values)
    conn.commit()

    return jsonify('User values updated'), 200

  else:
    return jsonify('No values sent in body'), 418


if __name__ == '__main__':
  create_all()
  app.run(port="4000")


