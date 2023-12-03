import { Request, Response, NextFunction } from "express";
import jwt from "jsonwebtoken";

const generateToken = (userId: number): string => {
  return jwt.sign({ userId }, process.env.JWT_SECRET, {
    expiresIn: "1d",
  });
};

export { generateToken };
