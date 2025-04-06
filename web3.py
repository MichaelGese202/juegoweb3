// Archivo principal del bot de Telegram para juego de minería Web3
const TelegramBot = require('node-telegram-bot-api');
const ethers = require('ethers');
const Web3 = require('web3');
require('dotenv').config();

// Configuración del bot y Web3
const token = process.env.TELEGRAM_BOT_TOKEN;
const bot = new TelegramBot(token, {polling: true});
const web3 = new Web3(process.env.WEB3_PROVIDER_URL);

// Dirección del contrato inteligente del juego
const GAME_CONTRACT_ADDRESS = process.env.GAME_CONTRACT_ADDRESS;
const GAME_ABI = require('./gameABI.json');

// Datos del juego
const gameData = {
  users: {},
  minerals: {
    copper: { name: "Cobre", value: 1, emoji: "🟤" },
    silver: { name: "Plata", value: 5, emoji: "⚪" },
    gold: { name: "Oro", value: 20, emoji: "🟡" },
    diamond: { name: "Diamante", value: 50, emoji: "💎" }
  },
  tools: {
    pickaxe: { name: "Pico", price: 50, power: 1, emoji: "⛏️" },
    drill: { name: "Taladro", price: 200, power: 3, emoji: "�drill" },
    excavator: { name: "Excavadora", price: 500, power: 7, emoji: "🚜" }
  }
};

// Función para inicializar usuario
function initUser(userId) {
  if (!gameData.users[userId]) {
    gameData.users[userId] = {
      wallet: null,
      balance: 10,
      inventory: {
        copper: 0,
        silver: 0,
        gold: 0,
        diamond: 0
      },
      tools: {
        pickaxe: 1,
        drill: 0,
        excavator: 0
      },
      energy: 100,
      lastMining: 0
    };
  }
  return gameData.users[userId];
}

// Función para conectar una wallet
async function connectWallet(userId, privateKey) {
  try {
    const wallet = new ethers.Wallet(privateKey);
    gameData.users[userId].wallet = wallet.address;
    return wallet.address;
  } catch (error) {
    console.error("Error al conectar wallet:", error);
    return null;
  }
}

// Función para minar
function mineResources(userId) {
  const user = gameData.users[userId];
  const currentTime = Date.now();
  
  // Verificar energía y tiempo de espera
  if (user.energy < 10) {
    return { success: false, message: "No tienes suficiente energía para minar. Espera a que se recargue." };
  }
  
  if (currentTime - user.lastMining < 30000) { // 30 segundos entre minados
    const timeLeft = Math.ceil((30000 - (currentTime - user.lastMining)) / 1000);
    return { success: false, message: `Tienes que esperar ${timeLeft} segundos más para volver a minar.` };
  }
  
  // Calcular poder de minería basado en herramientas
  const miningPower = 
    user.tools.pickaxe * gameData.tools.pickaxe.power +
    user.tools.drill * gameData.tools.drill.power +
    user.tools.excavator * gameData.tools.excavator.power;
  
  // Algoritmo de probabilidad de recursos
  const resources = {};
  let totalFound = 0;
  let resultMessage = "⛏️ ¡Has minado!\n\n";
  
  for (let i = 0; i < miningPower; i++) {
    const rand = Math.random() * 100;
    if (rand < 50) {
      resources.copper = (resources.copper || 0) + 1;
      totalFound++;
    } else if (rand < 80) {
      resources.silver = (resources.silver || 0) + 1;
      totalFound++;
    } else if (rand < 95) {
      resources.gold = (resources.gold || 0) + 1;
      totalFound++;
    } else {
      resources.diamond = (resources.diamond || 0) + 1;
      totalFound++;
    }
  }
  
  // Actualizar inventario del usuario
  Object.keys(resources).forEach(mineral => {
    user.inventory[mineral] += resources[mineral];
    resultMessage += `${gameData.minerals[mineral].emoji} ${gameData.minerals[mineral].name}: +${resources[mineral]}\n`;
  });
  
  // Actualizar estado del usuario
  user.energy -= 10;
  user.lastMining = currentTime;
  
  if (totalFound === 0) {
    resultMessage = "⛏️ Has minado pero no has encontrado nada. ¡Mejor suerte la próxima vez!";
  }
  
  return { success: true, message: resultMessage };
}

// Función para vender recursos
function sellResources(userId, mineralType, amount) {
  const user = gameData.users[userId];
  
  if (!gameData.minerals[mineralType]) {
    return { success: false, message: "Ese mineral no existe." };
  }
  
  if (!amount || amount <= 0) {
    return { success: false, message: "Debes vender al menos 1 unidad." };
  }
  
  if (user.inventory[mineralType] < amount) {
    return { success: false, message: `No tienes suficiente ${gameData.minerals[mineralType].name}.` };
  }
  
  const value = gameData.minerals[mineralType].value * amount;
  user.inventory[mineralType] -= amount;
  user.balance += value;
  
  return { 
    success: true, 
    message: `Has vendido ${amount} ${gameData.minerals[mineralType].name} por ${value} monedas.`
  };
}

// Función para comprar herramientas
function buyTool(userId, toolType) {
  const user = gameData.users[userId];
  
  if (!gameData.tools[toolType]) {
    return { success: false, message: "Esa herramienta no existe." };
  }
  
  const tool = gameData.tools[toolType];
  
  if (user.balance < tool.price) {
    return { success: false, message: `No tienes suficientes monedas. Necesitas ${tool.price}.` };
  }
  
  user.balance -= tool.price;
  user.tools[toolType] += 1;
  
  return { 
    success: true, 
    message: `Has comprado un/a ${tool.name} por ${tool.price} monedas.`
  };
}

// Comandos del bot
bot.onText(/\/start/, (msg) => {
  const userId = msg.from.id;
  initUser(userId);
  
  bot.sendMessage(userId, 
    "🎮 *¡Bienvenido al Juego de Minería Web3!* 🎮\n\n" +
    "Mina recursos, mejora tus herramientas y gana criptomonedas.\n\n" +
    "Comandos disponibles:\n" +
    "/mine - Minar recursos\n" +
    "/inventory - Ver tu inventario\n" +
    "/shop - Tienda de herramientas\n" +
    "/sell - Vender recursos\n" +
    "/wallet - Conectar tu wallet\n" +
    "/energy - Ver tu energía actual",
    { parse_mode: "Markdown" }
  );
});

bot.onText(/\/mine/, (msg) => {
  const userId = msg.from.id;
  const user = initUser(userId);
  
  const result = mineResources(userId);
  bot.sendMessage(userId, result.message);
});

bot.onText(/\/inventory/, (msg) => {
  const userId = msg.from.id;
  const user = initUser(userId);
  
  let message = "🎒 *Tu Inventario* 🎒\n\n";
  
  // Mostrar minerales
  message += "*Minerales:*\n";
  Object.keys(gameData.minerals).forEach(mineral => {
    message += `${gameData.minerals[mineral].emoji} ${gameData.minerals[mineral].name}: ${user.inventory[mineral]}\n`;
  });
  
  // Mostrar herramientas
  message += "\n*Herramientas:*\n";
  Object.keys(gameData.tools).forEach(tool => {
    message += `${gameData.tools[tool].emoji} ${gameData.tools[tool].name}: ${user.tools[tool]}\n`;
  });
  
  // Mostrar monedas
  message += `\n💰 Monedas: ${user.balance}`;
  
  // Mostrar wallet si está conectada
  if (user.wallet) {
    message += `\n👛 Wallet: ${user.wallet.substring(0, 6)}...${user.wallet.substring(user.wallet.length - 4)}`;
  }
  
  bot.sendMessage(userId, message, { parse_mode: "Markdown" });
});

bot.onText(/\/shop/, (msg) => {
  const userId = msg.from.id;
  const user = initUser(userId);
  
  let message = "🛒 *Tienda de Herramientas* 🛒\n\n";
  message += `Tu balance: ${user.balance} monedas\n\n`;
  
  Object.keys(gameData.tools).forEach(tool => {
    const toolData = gameData.tools[tool];
    message += `${toolData.emoji} *${toolData.name}*\n`;
    message += `Precio: ${toolData.price} monedas\n`;
    message += `Poder de minería: +${toolData.power}\n`;
    message += `Para comprar: /buy_${tool}\n\n`;
  });
  
  bot.sendMessage(userId, message, { parse_mode: "Markdown" });
});

bot.onText(/\/buy_(.+)/, (msg, match) => {
  const userId = msg.from.id;
  const toolType = match[1];
  const user = initUser(userId);
  
  const result = buyTool(userId, toolType);
  bot.sendMessage(userId, result.message);
});

bot.onText(/\/sell (.+) (.+)/, (msg, match) => {
  const userId = msg.from.id;
  const mineralType = match[1];
  const amount = parseInt(match[2]);
  const user = initUser(userId);
  
  const result = sellResources(userId, mineralType, amount);
  bot.sendMessage(userId, result.message);
});

bot.onText(/\/wallet (.+)/, async (msg, match) => {
  const userId = msg.from.id;
  const privateKey = match[1];
  const user = initUser(userId);
  
  const walletAddress = await connectWallet(userId, privateKey);
  if (walletAddress) {
    bot.sendMessage(userId, `✅ Wallet conectada correctamente. Tu dirección: ${walletAddress.substring(0, 6)}...${walletAddress.substring(walletAddress.length - 4)}`);
  } else {
    bot.sendMessage(userId, "❌ No se pudo conectar la wallet. Verifica que la clave privada sea correcta.");
  }
});

bot.onText(/\/energy/, (msg) => {
  const userId = msg.from.id;
  const user = initUser(userId);
  
  let energyMessage = `⚡ Energía actual: ${user.energy}/100\n\n`;
  
  if (user.energy < 100) {
    energyMessage += "Tu energía se recarga automáticamente con el tiempo.";
  }
  
  bot.sendMessage(userId, energyMessage);
});

// Contrato inteligente para transacciones Web3
const gameContractTemplate = `
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract MiningGame is ERC20, Ownable {
    mapping(address => uint256) public lastMiningTime;
    mapping(address => uint256) public playerLevel;
    
    uint256 public constant MINING_COOLDOWN = 1 hours;
    uint256 public constant BASE_REWARD = 10 * 10**18;
    
    constructor() ERC20("MiningToken", "MINE") {
        _mint(msg.sender, 1000000 * 10**18);
    }
    
    function mine() external {
        require(block.timestamp >= lastMiningTime[msg.sender] + MINING_COOLDOWN, "Mining cooldown not finished");
        
        uint256 reward = BASE_REWARD * (playerLevel[msg.sender] + 1);
        _mint(msg.sender, reward);
        
        lastMiningTime[msg.sender] = block.timestamp;
    }
    
    function upgradeLevel() external {
        uint256 cost = (playerLevel[msg.sender] + 1) * 100 * 10**18;
        require(balanceOf(msg.sender) >= cost, "Not enough tokens");
        
        _burn(msg.sender, cost);
        playerLevel[msg.sender] += 1;
    }
    
    function withdrawTokens(uint256 amount) external onlyOwner {
        _transfer(address(this), owner(), amount);
    }
}
`;

console.log('Bot de Telegram para juego de minería Web3 iniciado!');
