import { endOfDay, intervalToDuration } from "date-fns"
import Toastify from "toastify-js"

let tamilEntireWordList = []
let tamilMainWordList = []
let todaysWord = []
let keyList = []
let dayCount = 0
let currentWordLength = 4

let wordListsByLength = {
	3: { main: [], entire: [] },
	4: { main: [], entire: [] },
	5: { main: [], entire: [] },
}

const alphabets = [
	"q", "w", "e", "r", "t", "y", "u", "i", "o", "p",
	"a", "s", "d", "f", "g", "h", "j", "k", "l",
	"z", "x", "c", "v", "b", "n", "m",
]

const keyboard = document.querySelector(".keyboard")
const gamegrid = document.querySelector(".gamegrid")

const splitTamilWord = (word) => word.match(/[\u0b80-\u0bff][\u0bbe-\u0bcd\u0bd7]?/gi) || []

const getStorageKey = (key) => `${key}_${currentWordLength}`

// ----------------- Basic Function  ----------------- //
async function fetchBasics() {
	try {
		let data = await fetch("top_words.json")
		let json = await data.json()
		return json
	} catch (e) {
		let data = await fetch("words.json")
		let json = await data.json()
		return json
	}
}

function categorizeWords(datas) {
	datas.tamilMainWordList.forEach((wordArr) => {
		const len = wordArr.length
		if (wordListsByLength[len]) {
			wordListsByLength[len].main.push(wordArr)
		}
	})

	datas.tamilEntireWordList.forEach((wordStr) => {
		const letters = splitTamilWord(wordStr)
		const len = letters.length
		if (wordListsByLength[len]) {
			wordListsByLength[len].entire.push(wordStr)
		}
	})

	;[3, 4, 5].forEach((len) => {
		if (wordListsByLength[len].main.length < 10 && wordListsByLength[len].entire.length > 0) {
			wordListsByLength[len].main = wordListsByLength[len].entire.map((w) => splitTamilWord(w))
		}
	})
}

let loadedFullDictionaries = { 3: false, 4: false, 5: false }

async function loadFullLengthDictionary(length) {
	if (loadedFullDictionaries[length]) return
	try {
		const resp = await fetch(`words_${length}.json`)
		if (resp.ok) {
			const list = await resp.json()
			wordListsByLength[length].entire = list
			loadedFullDictionaries[length] = true
			console.log(`Loaded full dictionary for length ${length}: ${list.length} words`)
		}
	} catch (e) {
		console.log(`Could not load words_${length}.json:`, e)
	}
}

async function isItValidTamilWord(string) {
	const currentList = wordListsByLength[currentWordLength]?.entire || []
	if (currentList.includes(string) || tamilEntireWordList.includes(string)) {
		return true
	}
	if (!loadedFullDictionaries[currentWordLength]) {
		await loadFullLengthDictionary(currentWordLength)
		const updatedList = wordListsByLength[currentWordLength]?.entire || []
		if (updatedList.includes(string)) return true
	}
	try {
		const resp = await fetch(`https://iapi.glosbe.com/iapi3/wordlist?l1=ta&l2=en&q=${encodeURIComponent(string)}&after=1`)
		const data = await resp.json()
		if (data && data.after && data.after[0] && data.after[0].phrase) {
			const phrase = data.after[0].phrase
			if (phrase.split(" ").includes(string)) {
				return true
			}
		}
	} catch (e) {
		console.log("Glosbe API validation error:", e)
	}
	return false
}

function getDailyDayCount() {
	const epoch = Date.UTC(2024, 0, 1)
	const now = Date.now()
	const oneDay = 1000 * 60 * 60 * 24
	return Math.floor((now - epoch) / oneDay)
}

function createSeededRandom(seed) {
	let s = Math.abs(seed) % 233280
	return function () {
		s = (s * 9301 + 49297) % 233280
		return s / 233280
	}
}

function getDailyFeaturedWordLength() {
	const day = getDailyDayCount()
	const lengths = [3, 4, 5]
	const index = (day * 7 + 13) % lengths.length
	return lengths[index]
}

function getDevWordOverride() {
	try {
		let raw = new URLSearchParams(window.location.search).get("word")
		if (!raw && window.location.pathname.includes("word=")) {
			const parts = window.location.pathname.split("word=")
			if (parts[1]) raw = parts[1].split("/")[0].split("?")[0]
		}
		if (!raw) {
			raw = localStorage.getItem("debugWord")
		}
		if (raw) {
			const decoded = decodeURIComponent(raw)
			const letters = splitTamilWord(decoded)
			if (letters.length >= 3 && letters.length <= 5) {
				return { word: decoded, letters }
			}
		}
	} catch (e) {
		console.log("Dev word error:", e)
	}
	return null
}

function generateTodaysWord() {
	dayCount = getDailyDayCount()

	const dev = getDevWordOverride()
	if (dev) {
		currentWordLength = dev.letters.length
		console.log("🛠️ [Dev Mode] Overriding target word to:", dev.word, dev.letters)
		return dev.letters
	}

	const pool = wordListsByLength[currentWordLength]?.main || []
	if (!pool || pool.length === 0) return ["த", "மி", "ழ்"]

	const seed = (dayCount * 9301 + currentWordLength * 49297) % 233280
	const index = seed % pool.length
	return pool[index]
}

// Global Dev Console Helpers for Testing
window.setTestWord = (word) => {
	localStorage.setItem("debugWord", word)
	localStorage.removeItem(getStorageKey("tamilWordle"))
	localStorage.removeItem(getStorageKey("keyboard"))
	localStorage.removeItem(getStorageKey("timer"))
	console.log(`Test word set to "${word}". Local storage cleared. Reloading...`)
	location.reload()
}

window.clearTestWord = () => {
	localStorage.removeItem("debugWord")
	localStorage.removeItem(getStorageKey("tamilWordle"))
	localStorage.removeItem(getStorageKey("keyboard"))
	localStorage.removeItem(getStorageKey("timer"))
	console.log("Test word cleared. Local storage cleared. Reloading...")
	location.reload()
}

function renderGrid() {
	gamegrid.innerHTML = ""
	gamegrid.style.setProperty("--word-length", currentWordLength)
	const totalBoxes = currentWordLength * 8
	for (let i = 0; i < totalBoxes; i++) {
		const box = document.createElement("div")
		box.className = "box"
		gamegrid.appendChild(box)
	}
}

// ----------------- Helper Functions  ----------------- //

const activeTiles = () => gamegrid.querySelectorAll('[data-state="active"]')
const zero = (x) => ("0" + x).slice(-2)
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

// ----------------- Game Interaction  ----------------- //
function startGame() {
	const storage = JSON.parse(localStorage.getItem(getStorageKey("tamilWordle")))
	if (storage && storage.status !== "Win" && storage.status !== "Lose") {
		document.addEventListener("click", mouseInteraction)
		document.addEventListener("keydown", keyboardInteraction)
	}
}

function stopGame() {
	document.removeEventListener("click", mouseInteraction)
	document.removeEventListener("keydown", keyboardInteraction)
}

function mouseInteraction(e) {
	if (e.target.matches("[data-key]")) {
		enterText(e.target.dataset.key)
		return
	}
	if (e.target.matches("[data-enter]")) {
		onAnswerSubmit()
		return
	}
	if (e.target.matches("[data-delete]")) {
		deleteText()
		return
	}
}

function keyboardInteraction(e) {
	if (e.key == "Backspace") {
		deleteText()
		return
	}
	if (e.key == "Enter") {
		onAnswerSubmit()
		return
	}

	if (e.key.match(/^[a-z]$/)) {
		enterText(keyList[alphabets.indexOf(e.key.toLowerCase())])
		return
	}
	return
}

function scrollToActiveRow() {
	const container = document.querySelector(".gamegrid-container")
	if (!container) return
	const activeBox = gamegrid.querySelector(":not([data-letter])") || activeTiles()[0]
	if (activeBox) {
		activeBox.scrollIntoView({ behavior: "smooth", block: "nearest" })
	}
}

const VOWEL_TO_SIGN_MAP = {
	"அ": "",
	"ஆ": "ா",
	"இ": "ி",
	"ஈ": "ீ",
	"உ": "ு",
	"ஊ": "ூ",
	"எ": "ெ",
	"ஏ": "ே",
	"ஐ": "ை",
	"ஒ": "ொ",
	"ஓ": "ோ",
	"ஔ": "ௌ",
	"ஃ": "்",
}

const SIGN_TO_VOWEL_MAP = {
	"": "அ",
	"ா": "ஆ",
	"ி": "இ",
	"ீ": "ஈ",
	"ு": "உ",
	"ூ": "ஊ",
	"ெ": "எ",
	"ே": "ஏ",
	"ை": "ஐ",
	"ொ": "ஒ",
	"ோ": "ஓ",
	"ௌ": "ஔ",
	"்": "ஃ",
}

const CONSONANTS = ["க", "ங", "ச", "ஞ", "ட", "ண", "த", "ந", "ப", "ம", "ய", "ர", "ல", "வ", "ழ", "ள", "ற", "ன"]

function enterText(letter) {
	const active = activeTiles()
	const isVowelKey = Object.prototype.hasOwnProperty.call(VOWEL_TO_SIGN_MAP, letter)

	if (isVowelKey) {
		const lastTile = active[active.length - 1]
		if (lastTile && lastTile.dataset.letter) {
			const current = lastTile.dataset.letter
			const baseChar = [...current][0]
			const isBaseConsonant = CONSONANTS.includes(baseChar)

			if (isBaseConsonant) {
				const sign = VOWEL_TO_SIGN_MAP[letter]
				const combined = (baseChar + sign).normalize("NFC")
				lastTile.dataset.letter = combined
				lastTile.textContent = combined
				updateVowelKeyLabels()
				scrollToActiveRow()
				return
			}
		}
	}

	if (active.length >= currentWordLength) return
	var state = JSON.parse(localStorage.getItem(getStorageKey("timer")))
	if (!state) {
		localStorage.setItem(getStorageKey("timer"), JSON.stringify(new Date().getTime()))
	}
	const box = gamegrid.querySelector(":not([data-letter])")
	if (!box) return
	box.dataset.letter = letter
	box.textContent = letter
	box.dataset.state = "active"
	updateVowelKeyLabels()
	scrollToActiveRow()
}

function deleteText() {
	const active = activeTiles()
	const lastText = active[active.length - 1]
	if (lastText == null) return

	const chars = [...lastText.dataset.letter]
	if (chars.length > 1) {
		const base = chars[0]
		lastText.dataset.letter = base
		lastText.textContent = base
	} else {
		lastText.textContent = ""
		delete lastText.dataset.letter
		delete lastText.dataset.state
	}
	updateVowelKeyLabels()
	scrollToActiveRow()
}

const VOWEL_KEYS = ["அ", "ஆ", "இ", "ஈ", "உ", "ஊ", "எ", "ஏ", "ஐ", "ஒ", "ஓ", "ஔ", "ஃ"]

function getKeyStateMaps() {
	const storageKey = getStorageKey("tamilWordle")
	const storage = JSON.parse(localStorage.getItem(storageKey)) || {}
	const gameState = storage.gameState || []
	const dataStates = storage.data_states || []
	const exactGraphemeMap = {}
	const consonantBaseMap = {}

	const mergeState = (current, next) => {
		if (current === "correct") return "correct"
		if (current === "incorrect-location" && next !== "correct") return "incorrect-location"
		return next
	}

	const targetBases = todaysWord ? todaysWord.map((w) => getBaseAndVowel(w).base) : []

	gameState.forEach((row, rowIdx) => {
		if (Array.isArray(row) && dataStates[rowIdx]) {
			row.forEach((grapheme, colIdx) => {
				const state = dataStates[rowIdx][colIdx]
				if (grapheme && state) {
					exactGraphemeMap[grapheme] = mergeState(exactGraphemeMap[grapheme], state)

					const isStandalone = INDEPENDENT_VOWELS.includes(grapheme)
					if (!isStandalone) {
						const { base } = getBaseAndVowel(grapheme)
						if (base) {
							if (state === "incorrect" && targetBases.includes(base)) {
								consonantBaseMap[base] = mergeState(consonantBaseMap[base], "incorrect-location")
							} else {
								consonantBaseMap[base] = mergeState(consonantBaseMap[base], state)
							}
						}
					} else {
						consonantBaseMap[grapheme] = mergeState(consonantBaseMap[grapheme], state)
					}
				}
			})
		}
	})

	return { exactGraphemeMap, consonantBaseMap }
}

function resetVowelKeyLabels() {
	updateVowelKeyLabels()
}

function updateVowelKeyLabels() {
	const active = activeTiles()
	const lastTile = active[active.length - 1]
	const { exactGraphemeMap, consonantBaseMap } = getKeyStateMaps()

	let baseConsonant = null
	if (lastTile && lastTile.dataset.letter) {
		const current = lastTile.dataset.letter
		const baseChar = [...current][0]
		if (CONSONANTS.includes(baseChar)) {
			baseConsonant = baseChar
		}
	}

	CONSONANTS.forEach((cChar) => {
		const cKeyElem = keyboard.querySelector(`[data-key="${cChar}"]`)
		if (cKeyElem) {
			cKeyElem.classList.remove("correct", "incorrect", "incorrect-location")
			const st = consonantBaseMap[cChar] || exactGraphemeMap[cChar]
			if (st) {
				cKeyElem.classList.add(st)
			}
		}
	})

	VOWEL_KEYS.forEach((vowelChar) => {
		const keyElem = keyboard.querySelector(`[data-key="${vowelChar}"]`)
		if (!keyElem) return

		keyElem.classList.remove("vowel-combined", "correct", "incorrect", "incorrect-location")

		if (baseConsonant) {
			const sign = VOWEL_TO_SIGN_MAP[vowelChar]
			const combined = (baseConsonant + sign).normalize("NFC")
			keyElem.textContent = combined
			keyElem.classList.add("vowel-combined")

			const st = exactGraphemeMap[combined]
			if (st) {
				keyElem.classList.add(st)
			}
		} else {
			keyElem.textContent = vowelChar
			const st = exactGraphemeMap[vowelChar]
			if (st) {
				keyElem.classList.add(st)
			}
		}
	})
}

// ----------------- Game Setup & States ----------------- //

function setGameStats(stats = {}) {
	const statsKey = getStorageKey("tamilWordleStats")
	if (Object.keys(stats).length === 0) {
		if (!localStorage.getItem(statsKey)) {
			stats = {
				played: 0,
				wins: 0,
				streak: 0,
				lastWinTimeTaken: 0,
			}
		} else {
			stats = JSON.parse(localStorage.getItem(statsKey))
		}
	}
	localStorage.setItem(statsKey, JSON.stringify(stats))
	document.getElementById("played").innerHTML = stats.played
	document.getElementById("wins").innerHTML = stats.wins
	document.getElementById("streaks").innerHTML = stats.streak
	document.getElementById("timetaken").innerHTML = stats.lastWinTimeTaken
}

function setCurrentGameState(gameState, data_states) {
	gameState.forEach(async (word, wordIndex) => {
		if (word !== "") {
			word.forEach(async (tile, index) => {
				const box = gamegrid.querySelector(":not([data-letter])")
				if (!box) return
				box.dataset.letter = tile
				await sleep(100 * (index + 1))
				box.classList.add("reveal")
				await sleep(200 * (index + 1))
				const state = data_states[wordIndex][index]
				box.dataset.state = state

				const targetObj = getBaseAndVowel(todaysWord[index])
				const guessObj = getBaseAndVowel(tile)

				if (guessObj.base && targetObj.base && guessObj.base === targetObj.base) {
					box.dataset.consonantMatch = "true"
				} else {
					box.dataset.consonantMatch = "false"
				}

				if (guessObj.vowel && targetObj.vowel && guessObj.vowel === targetObj.vowel) {
					box.dataset.vowelMatch = "true"
				} else {
					box.dataset.vowelMatch = "false"
				}

				box.innerHTML = tile
				box.classList.remove("reveal")
			})
		}
	})
}

function freshDay() {
	localStorage.removeItem(getStorageKey("tamilWordle"))
	localStorage.removeItem(getStorageKey("keyboard"))
	localStorage.removeItem(getStorageKey("timer"))
	const storage = {
		gameState: ["", "", "", "", "", "", "", ""],
		data_states: [null, null, null, null, null, null, null, null],
		status: "Initiated",
		answer: todaysWord,
		expires: String(new Date()).slice(0, 15),
	}
	localStorage.setItem(getStorageKey("tamilWordle"), JSON.stringify(storage))
	setGameStats()
}

function setGuessedWord(userguess) {
	let storage = JSON.parse(localStorage.getItem(getStorageKey("tamilWordle")))
	let index = storage.gameState.indexOf("")
	storage.gameState[index] = userguess
	var datasets = []
	userguess.forEach((e, i) => {
		if (todaysWord[i] === e) {
			datasets.push("correct")
		} else if (todaysWord.includes(e)) {
			datasets.push("incorrect-location")
		} else {
			datasets.push("incorrect")
		}
	})
	storage["data_states"][index] = datasets
	storage.status = "Progress"
	localStorage.setItem(getStorageKey("tamilWordle"), JSON.stringify(storage))
}

function gameCompletedSetCurrentStats(condition) {
	const statsKey = getStorageKey("tamilWordleStats")
	let stats = JSON.parse(localStorage.getItem(statsKey)) || { played: 0, wins: 0, streak: 0, lastWinTimeTaken: 0 }
	stats.played++
	if (condition === "win") {
		stats.wins++
		stats.streak++
	} else {
		stats.streak = 0
	}
	let intervalDur = intervalToDuration({
		start: JSON.parse(localStorage.getItem(getStorageKey("timer"))) || new Date().getTime(),
		end: new Date().getTime(),
	})
	if (intervalDur.hours > 0) {
		stats.lastWinTimeTaken =
			zero(intervalDur.hours) + ":" + zero(intervalDur.minutes) + ":" + zero(intervalDur.seconds)
	} else {
		stats.lastWinTimeTaken = zero(intervalDur.minutes) + ":" + zero(intervalDur.seconds)
	}
	setGameStats(stats)
	localStorage.removeItem(getStorageKey("timer"))
}

// ----------------- Game Logic ----------------- //

const ROW_1 = ["அ", "ஆ", "இ", "ஈ", "க", "ச", "ட", "த", "ப", "ற"]
const ROW_2 = ["உ", "ஊ", "எ", "ஏ", "ங", "ஞ", "ண", "ந", "ம", "ன"]
const ROW_3 = ["ஐ", "ஒ", "ஓ", "ஔ", "ய", "ர", "ல", "வ", "ழ", "ள"]

function createKeys() {
	return [
		...ROW_1,
		...ROW_2,
		...ROW_3,
		"ஃ",
	]
}

function createKeyboard() {
	let keys = `<div class='overlayloader'><div class='spinner'></div></div>`
	const keyStateMap = (JSON.parse(localStorage.getItem(getStorageKey("keyboard"))) || {}).stateMap || {}

	const getKClass = (char) => {
		const st = keyStateMap[char]
		const typeClass = CONSONANTS.includes(char) ? "consonant-key" : "vowel-key"
		return st ? `${st} key ${typeClass}` : `key ${typeClass}`
	}

	// Row 1 (10 keys)
	keys += `<div class="keyboard-row grid-row">`
	ROW_1.forEach((char) => {
		keys += `<button class="${getKClass(char)}" data-key="${char}">${char}</button>`
	})
	keys += `</div>`

	// Row 2 (10 keys)
	keys += `<div class="keyboard-row grid-row">`
	ROW_2.forEach((char) => {
		keys += `<button class="${getKClass(char)}" data-key="${char}">${char}</button>`
	})
	keys += `</div>`

	// Row 3 (10 keys)
	keys += `<div class="keyboard-row grid-row">`
	ROW_3.forEach((char) => {
		keys += `<button class="${getKClass(char)}" data-key="${char}">${char}</button>`
	})
	keys += `</div>`

	// Row 4 (Bottom Row: ஃ, சரிபார், ⌫)
	keys += `<div class="keyboard-row bottom-row">`
	keys += `<button class="${getKClass("ஃ")} key special-single-key" data-key="ஃ">ஃ</button>`
	keys += `<button data-enter class="key special enter-key">சரிபார்</button>`
	keys += `<button data-delete aria-label='Delete Key' class="key special delete-key">
  <svg xmlns="http://www.w3.org/2000/svg" height="22" viewBox="0 0 24 24" width="22">
    <path fill="var(--color-tone-1)" d="M22 3H7c-.69 0-1.23.35-1.59.88L0 12l5.41 8.11c.36.53.9.89 1.59.89h15c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H7.07L2.4 12l4.66-7H22v14zm-11.59-2L14 13.41 17.59 17 19 15.59 15.41 12 19 8.41 17.59 7 14 10.59 10.41 7 9 8.41 12.59 12 9 15.59z"></path>
  </svg>
  </button>`
	keys += `</div>`

	return keys
}

function toast(msg) {
	Toastify({
		text: msg,
		duration: 3000,
		gravity: "top",
		position: "center",
		stopOnFocus: true,
		style: {
			background: "white",
			color: "black",
			fontWeight: "bold",
			display: "flex",
			alignItems: "center",
			justifyContent: "center",
			textAlign: "center",
		},
	}).showToast()
}

async function onAnswerSubmit() {
	let overloayloader = document.querySelector(".overlayloader")
	stopGame()
	const activeBox = [...activeTiles()]
	if (activeBox.length !== currentWordLength) {
		toast("Not enough letters")
		errorShake(activeBox)
		startGame()
		return
	} else {
		const userguess = activeBox.map((e) => e.dataset.letter)
		const isLocalValid = wordListsByLength[currentWordLength]?.entire.includes(userguess.join("")) || tamilEntireWordList.includes(userguess.join(""))
		if (!isLocalValid) {
			if (overloayloader) overloayloader.style.display = "flex"
			const checkInternet = await isItValidTamilWord(userguess.join(""))
			if (overloayloader) overloayloader.style.display = "none"
			if (!checkInternet) {
				toast("Not in word list")
				errorShake(activeBox)
				startGame()
				return
			}
		}
		setGuessedWord(userguess)
		resetVowelKeyLabels()
		activeTiles().forEach((...e) => {
			reveal(...e, userguess)
		})
	}
}

function checkAnswer(userguess, boxes) {
	let storageKey = getStorageKey("tamilWordle")
	let storage = JSON.parse(localStorage.getItem(storageKey))
	if (userguess.join("") === todaysWord.join("")) {
		toast("You Win!")
		winAnimate(boxes)
		stopGame()
		storage.status = "Win"
		localStorage.setItem(storageKey, JSON.stringify(storage))
		gameCompletedSetCurrentStats("win")
		setTimeout(() => {
			statsAvailable(true)
			document.getElementById("statistics").click()
		}, 1500)
		return
	}
	if (gamegrid.querySelectorAll(":not([data-letter])").length == 0) {
		toast(todaysWord.join(""))
		storage.status = "Lose"
		stopGame()
		gameCompletedSetCurrentStats("lose")
		setTimeout(() => {
			statsAvailable(true)
			document.getElementById("statistics").click()
		}, 1500)
	}
	localStorage.setItem(storageKey, JSON.stringify(storage))
}

// ---------------- Game Animations ---------------- //

function errorShake(box) {
	box.forEach((element) => {
		element.classList.add("shake")
		element.addEventListener(
			"animationend",
			function () {
				element.classList.remove("shake")
			},
			{ once: true }
		)
	})
}

const INDEPENDENT_VOWELS = ["அ", "ஆ", "இ", "ஈ", "உ", "ஊ", "எ", "ஏ", "ஐ", "ஒ", "ஓ", "ஔ", "ஃ"]

function getBaseAndVowel(grapheme) {
	if (!grapheme) return { base: "", vowel: null }
	const normalized = grapheme.trim().normalize("NFC")
	const chars = [...normalized]
	const base = chars[0]

	if (INDEPENDENT_VOWELS.includes(base)) {
		return { base: base, vowel: base }
	}

	const sign = chars.length > 1 ? chars.slice(1).join("") : ""
	const vowel = SIGN_TO_VOWEL_MAP[sign] || "அ"
	return { base: base, vowel: vowel }
}

function updateKeyState(char, state) {
	if (!char) return
	const keyboardKey = getStorageKey("keyboard")
	const Lkeyboard = JSON.parse(localStorage.getItem(keyboardKey)) || { stateMap: {} }
	if (!Lkeyboard.stateMap) Lkeyboard.stateMap = {}

	const currentState = Lkeyboard.stateMap[char]
	if (currentState === "correct") return
	if (currentState === "incorrect-location" && state === "incorrect") return

	Lkeyboard.stateMap[char] = state
	localStorage.setItem(keyboardKey, JSON.stringify(Lkeyboard))

	const keyElem = keyboard.querySelector(`[data-key="${char}"]`)
	if (keyElem) {
		keyElem.classList.remove("correct", "incorrect", "incorrect-location")
		keyElem.classList.add(state)
	}
}

function reveal(box, index, array, userguess) {
	const letter = box.dataset.letter
	setTimeout(() => {
		box.classList.add("reveal")
	}, (index * 500) / 2)

	box.addEventListener(
		"transitionend",
		() => {
			box.classList.remove("reveal")

			const targetBases = todaysWord.map((w) => getBaseAndVowel(w).base)
			const targetVowels = todaysWord.map((w) => getBaseAndVowel(w).vowel).filter(Boolean)

			const { base: gBase, vowel: gVowel } = getBaseAndVowel(letter)
			const targetObjAtIndex = getBaseAndVowel(todaysWord[index])

			const isStandaloneVowel = INDEPENDENT_VOWELS.includes(letter)

			if (todaysWord[index] === letter) {
				box.dataset.state = "correct"
				updateKeyState(letter, "correct")
				if (!isStandaloneVowel) {
					updateKeyState(gBase, "correct")
				}
			} else if (todaysWord.includes(letter)) {
				box.dataset.state = "incorrect-location"
				updateKeyState(letter, "incorrect-location")
				if (!isStandaloneVowel) {
					updateKeyState(gBase, "incorrect-location")
				}
			} else {
				box.dataset.state = "incorrect"
				updateKeyState(letter, "incorrect")

				if (!isStandaloneVowel) {
					// Base consonant evaluation
					if (targetBases.includes(gBase)) {
						updateKeyState(gBase, "incorrect-location")
					} else {
						updateKeyState(gBase, "incorrect")
					}
				}
			}

			if (gBase && targetObjAtIndex.base && gBase === targetObjAtIndex.base) {
				box.dataset.consonantMatch = "true"
			} else {
				box.dataset.consonantMatch = "false"
			}

			if (gVowel && targetObjAtIndex.vowel && gVowel === targetObjAtIndex.vowel) {
				box.dataset.vowelMatch = "true"
			} else {
				box.dataset.vowelMatch = "false"
			}

			if (index === todaysWord.length - 1) {
				box.addEventListener(
					"transitionend",
					() => {
						updateVowelKeyLabels()
						startGame()
						checkAnswer(userguess, array)
					},
					{ once: true }
				)
			}
		},
		{ once: true }
	)
}

function winAnimate(box) {
	box.forEach((element, index) => {
		setTimeout(() => {
			element.classList.add("winAnimate")
			element.addEventListener(
				"animationend",
				function () {
					element.classList.remove("winAnimate")
				},
				{ once: true }
			)
		}, (index * 500) / 5)
	})
}

// ----------------- UI functions ----------------- //

function showHelper() {
	stopGame()
	setTimeout(() => {
		document.querySelector(".helper").style.opacity = 1
	}, 10)
	document.querySelector(".helper").style.display = "flex"
}

function hideHelper() {
	document.querySelector(".helper").style.opacity = 0
	setTimeout(() => {
		document.querySelector(".helper").style.display = "none"
	}, 500)
	startGame()
}



function showStatistics() {
	stopGame()
	setTimeout(() => {
		document.querySelector(".statistics").style.opacity = 1
	}, 10)
	document.querySelector(".statistics").style.display = "flex"
}

function hideStatistics() {
	document.querySelector(".statistics").style.opacity = 0
	setTimeout(() => {
		document.querySelector(".statistics").style.display = "none"
	}, 500)
	startGame()
}

function showSettings() {
	stopGame()
	setTimeout(() => {
		document.querySelector(".settings").style.opacity = 1
	}, 10)
	document.querySelector(".settings").style.display = "flex"
}

function hideSettings() {
	document.querySelector(".settings").style.opacity = 0
	setTimeout(() => {
		document.querySelector(".settings").style.display = "none"
	}, 500)
	startGame()
}

function showFeedback() {
	stopGame()
	setTimeout(() => {
		document.querySelector(".feedback").style.opacity = 1
	}, 10)
	document.querySelector(".feedback").style.display = "flex"
}

function hideFeedback() {
	localStorage.setItem("tamilWordleFeedback", "true")
	document.querySelector(".feedback").style.opacity = 0
	setTimeout(() => {
		document.querySelector(".feedback").style.display = "none"
	}, 500)
	startGame()
}

function translateInstruction() {
	var switchBtn = document.getElementById("translateSwitch")
	let instructionsEng = document.getElementById("instructions-english")
	let instructionsTam = document.getElementById("instructions-tamil")
	var headingEng = document.getElementById("howtoplay-english")
	var headingTam = document.getElementById("howtoplay-tamil")
	if (switchBtn.checked) {
		instructionsTam.classList.remove("hidden")
		instructionsEng.classList.add("hidden")
		headingTam.classList.remove("hidden")
		headingEng.classList.add("hidden")
	} else {
		instructionsTam.classList.add("hidden")
		instructionsEng.classList.remove("hidden")
		headingTam.classList.add("hidden")
		headingEng.classList.remove("hidden")
	}
}

async function shareButton() {
	const storageKey = getStorageKey("tamilWordle")
	const tamilWordle = JSON.parse(localStorage.getItem(storageKey))
	if (!tamilWordle) return
	const data_states = tamilWordle["data_states"]
	const gameState = tamilWordle["gameState"]
	let attempts = "X"
	if (tamilWordle.status === "Win") {
		attempts = gameState.filter((x) => x !== "").length
	}
	let textShare = `தமிழ் Wordle (${currentWordLength} Letters)\nDay-${dayCount} Attempt-${attempts}/8 \n\n`
	data_states.forEach((row) => {
		if (row != null) {
			row.forEach((ans) => {
				ans === "correct" && (textShare += "🟢")
				ans === "incorrect" && (textShare += "⚪")
				ans === "incorrect-location" && (textShare += "🟡")
			})
			textShare += "\n"
		}
	})
	textShare += "\nPlay now at https://tamilwordle.in"
	if (navigator.share && !/(win32|win64|windows|wince)/i.test(navigator.platform)) {
		try {
			await navigator.share({ text: textShare })
		} catch (err) {
			console.log(err)
		}
	} else {
		navigator.clipboard.writeText(textShare)
		toast("Copied to clipboard")
	}
}

function setMode(mode) {
	if (mode === "dark") {
		document.body.classList.add("darkmode")
		document.getElementById("themeSwitch").classList.remove("day")
		document.querySelector(".moon").classList.remove("sun")
		localStorage.setItem("mode", "dark")
	} else {
		document.getElementById("themeSwitch").classList.add("day")
		document.querySelector(".moon").classList.add("sun")
		document.body.classList.remove("darkmode")
		localStorage.setItem("mode", "light")
	}
}

function switchTheme() {
	var mode = localStorage.getItem("mode")
	if (mode === "light") {
		setMode("dark")
	} else {
		setMode("light")
	}
}

function statsAvailable(available) {
	if (available) {
		document.querySelector(".statscontainer").style.display = "flex"
		document.querySelector(".statsbottombar").style.display = "flex"
		document.querySelector(".nostats").style.display = "none"
	} else {
		document.querySelector(".statscontainer").style.display = "none"
		document.querySelector(".statsbottombar").style.display = "none"
		document.querySelector(".nostats").style.display = "flex"
	}
}

function onFeedbackSubmit(e) {
	e.preventDefault()
	let feedbackForm = document.getElementById("feedbackForm")
	let rating = feedbackForm.querySelector('input[name="rating"]:checked')
	let feedback = "REMOVED FEEDBACK 🤐"
	if (!rating) {
		toast("Please select a rating")
		return
	}
	rating = rating.value
	let formdata = new FormData()
	formdata.append("entry.1755405700", rating)
	formdata.append("entry.553521465", feedback)
	fetch(
		"https://docs.google.com/forms/d/e/1FAIpQLSeRsae4AdgNirW15RPHBYgIG-7pNigCtpYgCfgVu2wnYqz-Iw/formResponse",
		{
			method: "POST",
			body: formdata,
			mode: "no-cors",
		}
	).then(() => {
		toast("Thank you for your feedback!")
		localStorage.setItem("tamilWordleFeedback", "true")
		hideFeedback()
		showStatistics()
	})
}

function nextNewWordTimer() {
	setInterval(() => {
		var END = endOfDay(new Date()).getTime()
		var now = new Date().getTime()
		var distance = END - now
		var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
		var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60))
		var seconds = Math.floor((distance % (1000 * 60)) / 1000)
		document.querySelector(".clock").innerHTML =
			zero(hours) + ":" + zero(minutes) + ":" + zero(seconds)
	}, 1000)
}

function initGameForCurrentLength() {
	stopGame()
	todaysWord = generateTodaysWord()
	loadFullLengthDictionary(currentWordLength)

	const dev = getDevWordOverride()
	const storageKey = getStorageKey("tamilWordle")

	if (dev) {
		freshDay()
		renderGrid()
		startGame()
	} else if (localStorage.getItem(storageKey)) {
		renderGrid()
		const storage = JSON.parse(localStorage.getItem(storageKey))
		if (storage.expires !== String(new Date()).slice(0, 15)) {
			freshDay()
			startGame()
		} else {
			setGameStats()
			setCurrentGameState(storage.gameState, storage.data_states)

			if (storage.status === "Progress" || storage.status === "Initiated") {
				startGame()
			}
			if (storage.status === "Win" || storage.status === "Lose") {
				setTimeout(() => {
					document.getElementById("statistics").click()
				}, 1500)
			}
		}
	} else {
		renderGrid()
		freshDay()
		startGame()
	}

	keyList = createKeys()
	keyboard.innerHTML = createKeyboard(keyList)
	updateVowelKeyLabels()

	const statsObj = JSON.parse(localStorage.getItem(getStorageKey("tamilWordleStats"))) || { played: 0 }
	statsAvailable(statsObj.played > 0)
	setTimeout(scrollToActiveRow, 300)
}

const getAppVersion = () => {
	if (typeof __APP_VERSION__ !== "undefined") {
		return __APP_VERSION__
	}
	const now = new Date()
	const year = now.getFullYear()
	const month = String(now.getMonth() + 1).padStart(2, "0")
	const day = String(now.getDate()).padStart(2, "0")
	const hours = String(now.getHours()).padStart(2, "0")
	const mins = String(now.getMinutes()).padStart(2, "0")
	return `v${year}.${month}.${day}-${hours}${mins}`
}

const CURRENT_APP_VERSION = getAppVersion()
const DATA_VERSION = 2

function migrateUserData() {
	[3, 4, 5].forEach((len) => {
		const statsKey = `tamilWordleStats_${len}`
		try {
			let stats = JSON.parse(localStorage.getItem(statsKey)) || null
			if (stats) {
				stats.version = DATA_VERSION
				stats.played = Number(stats.played) || 0
				stats.wins = Number(stats.wins) || 0
				stats.streak = Number(stats.streak) || 0
				stats.lastWinTimeTaken = stats.lastWinTimeTaken || "00:00"
				localStorage.setItem(statsKey, JSON.stringify(stats))
			}
		} catch (e) {
			console.log(`Error migrating stats for length ${len}:`, e)
		}

		const stateKey = `tamilWordle_${len}`
		try {
			let game = JSON.parse(localStorage.getItem(stateKey)) || null
			if (game && (!Array.isArray(game.gameState) || !Array.isArray(game.data_states))) {
				localStorage.removeItem(stateKey)
			}
		} catch (e) {
			localStorage.removeItem(stateKey)
		}
	})
}

function checkAppReleaseUpdate() {
	const lastVersion = localStorage.getItem("app_version")
	if (!lastVersion || lastVersion !== CURRENT_APP_VERSION) {
		console.log(`🚀 App release update detected: ${lastVersion || "legacy"} -> ${CURRENT_APP_VERSION}`)
		migrateUserData()
		localStorage.setItem("app_version", CURRENT_APP_VERSION)
		if (lastVersion) {
			toast(`App updated to v${CURRENT_APP_VERSION}`)
		}
	} else {
		migrateUserData()
	}
}

// ------------------ MAIN ------------------

async function main() {
	const datas = await fetchBasics()
	tamilEntireWordList = datas.tamilEntireWordList
	tamilMainWordList = datas.tamilMainWordList

	categorizeWords(datas)

	// Automatically set today's daily puzzle word length (3, 4, or 5 letters), with dev override support
	const dev = getDevWordOverride()
	if (dev) {
		currentWordLength = dev.letters.length
	} else {
		currentWordLength = getDailyFeaturedWordLength()
	}

	document.getElementById("helperButton").onclick = showHelper
	document.getElementById("hideHelper").onclick = hideHelper

	document.getElementById("statistics").onclick = showStatistics
	document.getElementById("hideStatistics").onclick = hideStatistics
	document.getElementById("hideFeedBack").onclick = hideFeedback
	document.getElementById("settingsButton").onclick = showSettings
	document.getElementById("hideSettings").onclick = hideSettings
	document.getElementById("translateSwitch").onclick = translateInstruction
	document.getElementById("shareBtn").onclick = shareButton
	document.getElementById("themeSwitch").onclick = switchTheme
	document.getElementById("feedbackForm").onsubmit = onFeedbackSubmit

	if (!localStorage.getItem("mode")) {
		localStorage.setItem("mode", "dark")
	} else {
		setMode(localStorage.getItem("mode"))
	}

	if (!localStorage.getItem("tamilWordleFeedback")) {
		localStorage.setItem("tamilWordleFeedback", "false")
	}

	const versionDisplay = document.getElementById("appVersionDisplay")
	if (versionDisplay) {
		versionDisplay.textContent = `Version ${CURRENT_APP_VERSION}`
	}

	const navbarVersion = document.getElementById("navbarVersion")
	if (navbarVersion) {
		navbarVersion.textContent = CURRENT_APP_VERSION
	}

	checkAppReleaseUpdate()
	initGameForCurrentLength()
	nextNewWordTimer()

	if ("serviceWorker" in navigator) {
		window.addEventListener("load", () => {
			navigator.serviceWorker.register("./sw.js").catch((err) => {
				console.log("Service Worker registration failed:", err)
			})
		})
	}
}

main()
