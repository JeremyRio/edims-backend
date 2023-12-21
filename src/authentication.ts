import { Request, Response, NextFunction } from "express";
import { UserWithoutPassword } from "./interface";
import jwt from "jsonwebtoken";

const generateToken = (user: UserWithoutPassword): string => {
  return jwt.sign({ user }, process.env.JWT_SECRET, {
    expiresIn: "1d",
  });
};

const verifyToken = (req: Request, res: Response, next: NextFunction) => {
  // Get the token from the request header
  const token = req.headers.authorization?.split(" ")[1]; // Assumes Bearer token

  if (!token) {
    return res
      .status(401)
      .json({ message: "Access denied. No token provided." });
  }
  try {
    // Verify token
    const decoded = jwt.verify(token, process.env.JWT_SECRET!);
    const userReq = req as Request & { user: UserWithoutPassword };
    userReq.user = decoded as UserWithoutPassword;
    next(); // Proceed to the next middleware/route handler
  } catch (error) {
    res.status(400).json({ message: "Invalid token." });
  }
};

export { generateToken, verifyToken };
