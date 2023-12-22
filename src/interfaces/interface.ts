/**
 * components:
  schemas:
    User:
      type: object
      properties:
        username:
          type: string
        email:
          type: string
          format: email
        password:
          type: string
          format: password
      required:
        - username
        - email
        - password

    UserWithoutPassword:
      type: object
      properties:
        id:
          type: integer
          format: int64
        username:
          type: string
        email:
          type: string
          format: email
      required:
        - id
        - username
        - email

    LoginCredentials:
      type: object
      properties:
        email:
          type: string
          format: email
        password:
          type: string
          format: password
      required:
        - email
        - password

    Item:
      type: object
      properties:
        id:
          type: integer
          format: int64
        userid:
          type: integer
          format: int64
        name:
          type: string
        image:
          type: string
        category:
          type: string
        date:
          type: string
      required:
        - id
        - userid
        - name
        - image
        - category
        - date
 */

export interface User {
  username: string;
  email: string;
  password: string;
}

export interface UserWithoutPassword {
  id: number;
  username: string;
  email: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface Item {
  id: number;
  userid: number;
  name: string;
  image: string;
  category: string;
  date: string;
}
