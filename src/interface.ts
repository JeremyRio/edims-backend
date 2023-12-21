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
