// node_modules/sigma/dist/inherits-d1a1e29b.esm.js
function _toPrimitive(t, r) {
  if ("object" != typeof t || !t) return t;
  var e = t[Symbol.toPrimitive];
  if (void 0 !== e) {
    var i = e.call(t, r || "default");
    if ("object" != typeof i) return i;
    throw new TypeError("@@toPrimitive must return a primitive value.");
  }
  return ("string" === r ? String : Number)(t);
}
function _toPropertyKey(t) {
  var i = _toPrimitive(t, "string");
  return "symbol" == typeof i ? i : i + "";
}
function _classCallCheck(a, n) {
  if (!(a instanceof n)) throw new TypeError("Cannot call a class as a function");
}
function _defineProperties(e, r) {
  for (var t = 0; t < r.length; t++) {
    var o = r[t];
    o.enumerable = o.enumerable || false, o.configurable = true, "value" in o && (o.writable = true), Object.defineProperty(e, _toPropertyKey(o.key), o);
  }
}
function _createClass(e, r, t) {
  return r && _defineProperties(e.prototype, r), t && _defineProperties(e, t), Object.defineProperty(e, "prototype", {
    writable: false
  }), e;
}
function _getPrototypeOf(t) {
  return _getPrototypeOf = Object.setPrototypeOf ? Object.getPrototypeOf.bind() : function(t2) {
    return t2.__proto__ || Object.getPrototypeOf(t2);
  }, _getPrototypeOf(t);
}
function _isNativeReflectConstruct() {
  try {
    var t = !Boolean.prototype.valueOf.call(Reflect.construct(Boolean, [], function() {
    }));
  } catch (t2) {
  }
  return (_isNativeReflectConstruct = function() {
    return !!t;
  })();
}
function _assertThisInitialized(e) {
  if (void 0 === e) throw new ReferenceError("this hasn't been initialised - super() hasn't been called");
  return e;
}
function _possibleConstructorReturn(t, e) {
  if (e && ("object" == typeof e || "function" == typeof e)) return e;
  if (void 0 !== e) throw new TypeError("Derived constructors may only return object or undefined");
  return _assertThisInitialized(t);
}
function _callSuper(t, o, e) {
  return o = _getPrototypeOf(o), _possibleConstructorReturn(t, _isNativeReflectConstruct() ? Reflect.construct(o, e || [], _getPrototypeOf(t).constructor) : o.apply(t, e));
}
function _setPrototypeOf(t, e) {
  return _setPrototypeOf = Object.setPrototypeOf ? Object.setPrototypeOf.bind() : function(t2, e2) {
    return t2.__proto__ = e2, t2;
  }, _setPrototypeOf(t, e);
}
function _inherits(t, e) {
  if ("function" != typeof e && null !== e) throw new TypeError("Super expression must either be null or a function");
  t.prototype = Object.create(e && e.prototype, {
    constructor: {
      value: t,
      writable: true,
      configurable: true
    }
  }), Object.defineProperty(t, "prototype", {
    writable: false
  }), e && _setPrototypeOf(t, e);
}

// node_modules/sigma/dist/colors-beb06eb2.esm.js
function _arrayWithHoles(r) {
  if (Array.isArray(r)) return r;
}
function _iterableToArrayLimit(r, l) {
  var t = null == r ? null : "undefined" != typeof Symbol && r[Symbol.iterator] || r["@@iterator"];
  if (null != t) {
    var e, n, i, u, a = [], f = true, o = false;
    try {
      if (i = (t = t.call(r)).next, 0 === l) {
        if (Object(t) !== t) return;
        f = false;
      } else for (; !(f = (e = i.call(t)).done) && (a.push(e.value), a.length !== l); f = true) ;
    } catch (r2) {
      o = true, n = r2;
    } finally {
      try {
        if (!f && null != t.return && (u = t.return(), Object(u) !== u)) return;
      } finally {
        if (o) throw n;
      }
    }
    return a;
  }
}
function _arrayLikeToArray(r, a) {
  (null == a || a > r.length) && (a = r.length);
  for (var e = 0, n = Array(a); e < a; e++) n[e] = r[e];
  return n;
}
function _unsupportedIterableToArray(r, a) {
  if (r) {
    if ("string" == typeof r) return _arrayLikeToArray(r, a);
    var t = {}.toString.call(r).slice(8, -1);
    return "Object" === t && r.constructor && (t = r.constructor.name), "Map" === t || "Set" === t ? Array.from(r) : "Arguments" === t || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t) ? _arrayLikeToArray(r, a) : void 0;
  }
}
function _nonIterableRest() {
  throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function _slicedToArray(r, e) {
  return _arrayWithHoles(r) || _iterableToArrayLimit(r, e) || _unsupportedIterableToArray(r, e) || _nonIterableRest();
}
var HTML_COLORS = {
  black: "#000000",
  silver: "#C0C0C0",
  gray: "#808080",
  grey: "#808080",
  white: "#FFFFFF",
  maroon: "#800000",
  red: "#FF0000",
  purple: "#800080",
  fuchsia: "#FF00FF",
  green: "#008000",
  lime: "#00FF00",
  olive: "#808000",
  yellow: "#FFFF00",
  navy: "#000080",
  blue: "#0000FF",
  teal: "#008080",
  aqua: "#00FFFF",
  darkblue: "#00008B",
  mediumblue: "#0000CD",
  darkgreen: "#006400",
  darkcyan: "#008B8B",
  deepskyblue: "#00BFFF",
  darkturquoise: "#00CED1",
  mediumspringgreen: "#00FA9A",
  springgreen: "#00FF7F",
  cyan: "#00FFFF",
  midnightblue: "#191970",
  dodgerblue: "#1E90FF",
  lightseagreen: "#20B2AA",
  forestgreen: "#228B22",
  seagreen: "#2E8B57",
  darkslategray: "#2F4F4F",
  darkslategrey: "#2F4F4F",
  limegreen: "#32CD32",
  mediumseagreen: "#3CB371",
  turquoise: "#40E0D0",
  royalblue: "#4169E1",
  steelblue: "#4682B4",
  darkslateblue: "#483D8B",
  mediumturquoise: "#48D1CC",
  indigo: "#4B0082",
  darkolivegreen: "#556B2F",
  cadetblue: "#5F9EA0",
  cornflowerblue: "#6495ED",
  rebeccapurple: "#663399",
  mediumaquamarine: "#66CDAA",
  dimgray: "#696969",
  dimgrey: "#696969",
  slateblue: "#6A5ACD",
  olivedrab: "#6B8E23",
  slategray: "#708090",
  slategrey: "#708090",
  lightslategray: "#778899",
  lightslategrey: "#778899",
  mediumslateblue: "#7B68EE",
  lawngreen: "#7CFC00",
  chartreuse: "#7FFF00",
  aquamarine: "#7FFFD4",
  skyblue: "#87CEEB",
  lightskyblue: "#87CEFA",
  blueviolet: "#8A2BE2",
  darkred: "#8B0000",
  darkmagenta: "#8B008B",
  saddlebrown: "#8B4513",
  darkseagreen: "#8FBC8F",
  lightgreen: "#90EE90",
  mediumpurple: "#9370DB",
  darkviolet: "#9400D3",
  palegreen: "#98FB98",
  darkorchid: "#9932CC",
  yellowgreen: "#9ACD32",
  sienna: "#A0522D",
  brown: "#A52A2A",
  darkgray: "#A9A9A9",
  darkgrey: "#A9A9A9",
  lightblue: "#ADD8E6",
  greenyellow: "#ADFF2F",
  paleturquoise: "#AFEEEE",
  lightsteelblue: "#B0C4DE",
  powderblue: "#B0E0E6",
  firebrick: "#B22222",
  darkgoldenrod: "#B8860B",
  mediumorchid: "#BA55D3",
  rosybrown: "#BC8F8F",
  darkkhaki: "#BDB76B",
  mediumvioletred: "#C71585",
  indianred: "#CD5C5C",
  peru: "#CD853F",
  chocolate: "#D2691E",
  tan: "#D2B48C",
  lightgray: "#D3D3D3",
  lightgrey: "#D3D3D3",
  thistle: "#D8BFD8",
  orchid: "#DA70D6",
  goldenrod: "#DAA520",
  palevioletred: "#DB7093",
  crimson: "#DC143C",
  gainsboro: "#DCDCDC",
  plum: "#DDA0DD",
  burlywood: "#DEB887",
  lightcyan: "#E0FFFF",
  lavender: "#E6E6FA",
  darksalmon: "#E9967A",
  violet: "#EE82EE",
  palegoldenrod: "#EEE8AA",
  lightcoral: "#F08080",
  khaki: "#F0E68C",
  aliceblue: "#F0F8FF",
  honeydew: "#F0FFF0",
  azure: "#F0FFFF",
  sandybrown: "#F4A460",
  wheat: "#F5DEB3",
  beige: "#F5F5DC",
  whitesmoke: "#F5F5F5",
  mintcream: "#F5FFFA",
  ghostwhite: "#F8F8FF",
  salmon: "#FA8072",
  antiquewhite: "#FAEBD7",
  linen: "#FAF0E6",
  lightgoldenrodyellow: "#FAFAD2",
  oldlace: "#FDF5E6",
  magenta: "#FF00FF",
  deeppink: "#FF1493",
  orangered: "#FF4500",
  tomato: "#FF6347",
  hotpink: "#FF69B4",
  coral: "#FF7F50",
  darkorange: "#FF8C00",
  lightsalmon: "#FFA07A",
  orange: "#FFA500",
  lightpink: "#FFB6C1",
  pink: "#FFC0CB",
  gold: "#FFD700",
  peachpuff: "#FFDAB9",
  navajowhite: "#FFDEAD",
  moccasin: "#FFE4B5",
  bisque: "#FFE4C4",
  mistyrose: "#FFE4E1",
  blanchedalmond: "#FFEBCD",
  papayawhip: "#FFEFD5",
  lavenderblush: "#FFF0F5",
  seashell: "#FFF5EE",
  cornsilk: "#FFF8DC",
  lemonchiffon: "#FFFACD",
  floralwhite: "#FFFAF0",
  snow: "#FFFAFA",
  lightyellow: "#FFFFE0",
  ivory: "#FFFFF0"
};
var INT8 = new Int8Array(4);
var INT32 = new Int32Array(INT8.buffer, 0, 1);
var FLOAT32 = new Float32Array(INT8.buffer, 0, 1);
var RGBA_TEST_REGEX = /^\s*rgba?\s*\(/;
var RGBA_EXTRACT_REGEX = /^\s*rgba?\s*\(\s*([0-9]*)\s*,\s*([0-9]*)\s*,\s*([0-9]*)(?:\s*,\s*(.*)?)?\)\s*$/;
function parseColor(val) {
  var r = 0;
  var g = 0;
  var b = 0;
  var a = 1;
  if (val[0] === "#") {
    if (val.length === 4) {
      r = parseInt(val.charAt(1) + val.charAt(1), 16);
      g = parseInt(val.charAt(2) + val.charAt(2), 16);
      b = parseInt(val.charAt(3) + val.charAt(3), 16);
    } else {
      r = parseInt(val.charAt(1) + val.charAt(2), 16);
      g = parseInt(val.charAt(3) + val.charAt(4), 16);
      b = parseInt(val.charAt(5) + val.charAt(6), 16);
    }
    if (val.length === 9) {
      a = parseInt(val.charAt(7) + val.charAt(8), 16) / 255;
    }
  } else if (RGBA_TEST_REGEX.test(val)) {
    var match = val.match(RGBA_EXTRACT_REGEX);
    if (match) {
      r = +match[1];
      g = +match[2];
      b = +match[3];
      if (match[4]) a = +match[4];
    }
  }
  return {
    r,
    g,
    b,
    a
  };
}
var FLOAT_COLOR_CACHE = {};
for (htmlColor in HTML_COLORS) {
  FLOAT_COLOR_CACHE[htmlColor] = floatColor(HTML_COLORS[htmlColor]);
  FLOAT_COLOR_CACHE[HTML_COLORS[htmlColor]] = FLOAT_COLOR_CACHE[htmlColor];
}
var htmlColor;
function rgbaToFloat(r, g, b, a, masking) {
  INT32[0] = a << 24 | b << 16 | g << 8 | r;
  if (masking) INT32[0] = INT32[0] & 4278190079;
  return FLOAT32[0];
}
function floatColor(val) {
  val = val.toLowerCase();
  if (typeof FLOAT_COLOR_CACHE[val] !== "undefined") return FLOAT_COLOR_CACHE[val];
  var parsed = parseColor(val);
  var r = parsed.r, g = parsed.g, b = parsed.b;
  var a = parsed.a;
  a = a * 255 | 0;
  var color = rgbaToFloat(r, g, b, a, true);
  FLOAT_COLOR_CACHE[val] = color;
  return color;
}
var FLOAT_INDEX_CACHE = {};
function indexToColor(index) {
  if (typeof FLOAT_INDEX_CACHE[index] !== "undefined") return FLOAT_INDEX_CACHE[index];
  var r = (index & 16711680) >>> 16;
  var g = (index & 65280) >>> 8;
  var b = index & 255;
  var a = 255;
  var color = rgbaToFloat(r, g, b, a, true);
  FLOAT_INDEX_CACHE[index] = color;
  return color;
}
function colorToIndex(r, g, b, _a) {
  return b + (g << 8) + (r << 16);
}
function getPixelColor(gl, frameBuffer, x, y, pixelRatio, downSizingRatio) {
  var bufferX = Math.floor(x / downSizingRatio * pixelRatio);
  var bufferY = Math.floor(gl.drawingBufferHeight / downSizingRatio - y / downSizingRatio * pixelRatio);
  var pixel = new Uint8Array(4);
  gl.bindFramebuffer(gl.FRAMEBUFFER, frameBuffer);
  gl.readPixels(bufferX, bufferY, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, pixel);
  var _pixel = _slicedToArray(pixel, 4), r = _pixel[0], g = _pixel[1], b = _pixel[2], a = _pixel[3];
  return [r, g, b, a];
}

// node_modules/sigma/dist/index-236c62ad.esm.js
function _defineProperty(e, r, t) {
  return (r = _toPropertyKey(r)) in e ? Object.defineProperty(e, r, {
    value: t,
    enumerable: true,
    configurable: true,
    writable: true
  }) : e[r] = t, e;
}
function ownKeys(e, r) {
  var t = Object.keys(e);
  if (Object.getOwnPropertySymbols) {
    var o = Object.getOwnPropertySymbols(e);
    r && (o = o.filter(function(r2) {
      return Object.getOwnPropertyDescriptor(e, r2).enumerable;
    })), t.push.apply(t, o);
  }
  return t;
}
function _objectSpread2(e) {
  for (var r = 1; r < arguments.length; r++) {
    var t = null != arguments[r] ? arguments[r] : {};
    r % 2 ? ownKeys(Object(t), true).forEach(function(r2) {
      _defineProperty(e, r2, t[r2]);
    }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(t)) : ownKeys(Object(t)).forEach(function(r2) {
      Object.defineProperty(e, r2, Object.getOwnPropertyDescriptor(t, r2));
    });
  }
  return e;
}
function _superPropBase(t, o) {
  for (; !{}.hasOwnProperty.call(t, o) && null !== (t = _getPrototypeOf(t)); ) ;
  return t;
}
function _get() {
  return _get = "undefined" != typeof Reflect && Reflect.get ? Reflect.get.bind() : function(e, t, r) {
    var p = _superPropBase(e, t);
    if (p) {
      var n = Object.getOwnPropertyDescriptor(p, t);
      return n.get ? n.get.call(arguments.length < 3 ? e : r) : n.value;
    }
  }, _get.apply(null, arguments);
}
function _superPropGet(t, o, e, r) {
  var p = _get(_getPrototypeOf(1 & r ? t.prototype : t), o, e);
  return 2 & r && "function" == typeof p ? function(t2) {
    return p.apply(e, t2);
  } : p;
}
function getAttributeItemsCount(attr) {
  return attr.normalized ? 1 : attr.size;
}
function getAttributesItemsCount(attrs) {
  var res = 0;
  attrs.forEach(function(attr) {
    return res += getAttributeItemsCount(attr);
  });
  return res;
}
function loadShader(type, gl, source) {
  var glType = type === "VERTEX" ? gl.VERTEX_SHADER : gl.FRAGMENT_SHADER;
  var shader = gl.createShader(glType);
  if (shader === null) {
    throw new Error("loadShader: error while creating the shader");
  }
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  var successfullyCompiled = gl.getShaderParameter(shader, gl.COMPILE_STATUS);
  if (!successfullyCompiled) {
    var infoLog = gl.getShaderInfoLog(shader);
    gl.deleteShader(shader);
    throw new Error("loadShader: error while compiling the shader:\n".concat(infoLog, "\n").concat(source));
  }
  return shader;
}
function loadVertexShader(gl, source) {
  return loadShader("VERTEX", gl, source);
}
function loadFragmentShader(gl, source) {
  return loadShader("FRAGMENT", gl, source);
}
function loadProgram(gl, shaders) {
  var program = gl.createProgram();
  if (program === null) {
    throw new Error("loadProgram: error while creating the program.");
  }
  var i, l;
  for (i = 0, l = shaders.length; i < l; i++) gl.attachShader(program, shaders[i]);
  gl.linkProgram(program);
  var successfullyLinked = gl.getProgramParameter(program, gl.LINK_STATUS);
  if (!successfullyLinked) {
    gl.deleteProgram(program);
    throw new Error("loadProgram: error while linking the program.");
  }
  return program;
}
function killProgram(_ref) {
  var gl = _ref.gl, buffer = _ref.buffer, program = _ref.program, vertexShader = _ref.vertexShader, fragmentShader = _ref.fragmentShader;
  gl.deleteShader(vertexShader);
  gl.deleteShader(fragmentShader);
  gl.deleteProgram(program);
  gl.deleteBuffer(buffer);
}
function numberToGLSLFloat(n) {
  return n % 1 === 0 ? n.toFixed(1) : n.toString();
}
var PICKING_PREFIX = "#define PICKING_MODE\n";
var SIZE_FACTOR_PER_ATTRIBUTE_TYPE = _defineProperty(_defineProperty(_defineProperty(_defineProperty(_defineProperty(_defineProperty(_defineProperty(_defineProperty({}, WebGL2RenderingContext.BOOL, 1), WebGL2RenderingContext.BYTE, 1), WebGL2RenderingContext.UNSIGNED_BYTE, 1), WebGL2RenderingContext.SHORT, 2), WebGL2RenderingContext.UNSIGNED_SHORT, 2), WebGL2RenderingContext.INT, 4), WebGL2RenderingContext.UNSIGNED_INT, 4), WebGL2RenderingContext.FLOAT, 4);
var AbstractProgram = _createClass(function AbstractProgram2(_gl, _pickGl, _renderer) {
  _classCallCheck(this, AbstractProgram2);
});
var Program = (function() {
  function Program2(gl, pickingBuffer, renderer) {
    _classCallCheck(this, Program2);
    _defineProperty(this, "array", new Float32Array());
    _defineProperty(this, "constantArray", new Float32Array());
    _defineProperty(this, "capacity", 0);
    _defineProperty(this, "verticesCount", 0);
    var def = this.getDefinition();
    this.VERTICES = def.VERTICES;
    this.VERTEX_SHADER_SOURCE = def.VERTEX_SHADER_SOURCE;
    this.FRAGMENT_SHADER_SOURCE = def.FRAGMENT_SHADER_SOURCE;
    this.UNIFORMS = def.UNIFORMS;
    this.ATTRIBUTES = def.ATTRIBUTES;
    this.METHOD = def.METHOD;
    this.CONSTANT_ATTRIBUTES = "CONSTANT_ATTRIBUTES" in def ? def.CONSTANT_ATTRIBUTES : [];
    this.CONSTANT_DATA = "CONSTANT_DATA" in def ? def.CONSTANT_DATA : [];
    this.isInstanced = "CONSTANT_ATTRIBUTES" in def;
    this.ATTRIBUTES_ITEMS_COUNT = getAttributesItemsCount(this.ATTRIBUTES);
    this.STRIDE = this.VERTICES * this.ATTRIBUTES_ITEMS_COUNT;
    this.renderer = renderer;
    this.normalProgram = this.getProgramInfo("normal", gl, def.VERTEX_SHADER_SOURCE, def.FRAGMENT_SHADER_SOURCE, null);
    this.pickProgram = pickingBuffer ? this.getProgramInfo("pick", gl, PICKING_PREFIX + def.VERTEX_SHADER_SOURCE, PICKING_PREFIX + def.FRAGMENT_SHADER_SOURCE, pickingBuffer) : null;
    if (this.isInstanced) {
      var constantAttributesItemsCount = getAttributesItemsCount(this.CONSTANT_ATTRIBUTES);
      if (this.CONSTANT_DATA.length !== this.VERTICES) throw new Error("Program: error while getting constant data (expected ".concat(this.VERTICES, " items, received ").concat(this.CONSTANT_DATA.length, " instead)"));
      this.constantArray = new Float32Array(this.CONSTANT_DATA.length * constantAttributesItemsCount);
      for (var i = 0; i < this.CONSTANT_DATA.length; i++) {
        var vector = this.CONSTANT_DATA[i];
        if (vector.length !== constantAttributesItemsCount) throw new Error("Program: error while getting constant data (one vector has ".concat(vector.length, " items instead of ").concat(constantAttributesItemsCount, ")"));
        for (var j = 0; j < vector.length; j++) this.constantArray[i * constantAttributesItemsCount + j] = vector[j];
      }
      this.STRIDE = this.ATTRIBUTES_ITEMS_COUNT;
    }
  }
  return _createClass(Program2, [{
    key: "kill",
    value: function kill() {
      killProgram(this.normalProgram);
      if (this.pickProgram) {
        killProgram(this.pickProgram);
        this.pickProgram = null;
      }
    }
  }, {
    key: "getProgramInfo",
    value: function getProgramInfo(name, gl, vertexShaderSource, fragmentShaderSource, frameBuffer) {
      var def = this.getDefinition();
      var buffer = gl.createBuffer();
      if (buffer === null) throw new Error("Program: error while creating the WebGL buffer.");
      var vertexShader = loadVertexShader(gl, vertexShaderSource);
      var fragmentShader = loadFragmentShader(gl, fragmentShaderSource);
      var program = loadProgram(gl, [vertexShader, fragmentShader]);
      var uniformLocations = {};
      def.UNIFORMS.forEach(function(uniformName) {
        var location = gl.getUniformLocation(program, uniformName);
        if (location) uniformLocations[uniformName] = location;
      });
      var attributeLocations = {};
      def.ATTRIBUTES.forEach(function(attr) {
        attributeLocations[attr.name] = gl.getAttribLocation(program, attr.name);
      });
      var constantBuffer;
      if ("CONSTANT_ATTRIBUTES" in def) {
        def.CONSTANT_ATTRIBUTES.forEach(function(attr) {
          attributeLocations[attr.name] = gl.getAttribLocation(program, attr.name);
        });
        constantBuffer = gl.createBuffer();
        if (constantBuffer === null) throw new Error("Program: error while creating the WebGL constant buffer.");
      }
      return {
        name,
        program,
        gl,
        frameBuffer,
        buffer,
        constantBuffer: constantBuffer || {},
        uniformLocations,
        attributeLocations,
        isPicking: name === "pick",
        vertexShader,
        fragmentShader
      };
    }
  }, {
    key: "bindProgram",
    value: function bindProgram(program) {
      var _this = this;
      var offset = 0;
      var gl = program.gl, buffer = program.buffer;
      if (!this.isInstanced) {
        gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
        offset = 0;
        this.ATTRIBUTES.forEach(function(attr) {
          return offset += _this.bindAttribute(attr, program, offset);
        });
        gl.bufferData(gl.ARRAY_BUFFER, this.array, gl.DYNAMIC_DRAW);
      } else {
        gl.bindBuffer(gl.ARRAY_BUFFER, program.constantBuffer);
        offset = 0;
        this.CONSTANT_ATTRIBUTES.forEach(function(attr) {
          return offset += _this.bindAttribute(attr, program, offset, false);
        });
        gl.bufferData(gl.ARRAY_BUFFER, this.constantArray, gl.STATIC_DRAW);
        gl.bindBuffer(gl.ARRAY_BUFFER, program.buffer);
        offset = 0;
        this.ATTRIBUTES.forEach(function(attr) {
          return offset += _this.bindAttribute(attr, program, offset, true);
        });
        gl.bufferData(gl.ARRAY_BUFFER, this.array, gl.DYNAMIC_DRAW);
      }
      gl.bindBuffer(gl.ARRAY_BUFFER, null);
    }
  }, {
    key: "unbindProgram",
    value: function unbindProgram(program) {
      var _this2 = this;
      if (!this.isInstanced) {
        this.ATTRIBUTES.forEach(function(attr) {
          return _this2.unbindAttribute(attr, program);
        });
      } else {
        this.CONSTANT_ATTRIBUTES.forEach(function(attr) {
          return _this2.unbindAttribute(attr, program, false);
        });
        this.ATTRIBUTES.forEach(function(attr) {
          return _this2.unbindAttribute(attr, program, true);
        });
      }
    }
  }, {
    key: "bindAttribute",
    value: function bindAttribute(attr, program, offset, setDivisor) {
      var sizeFactor = SIZE_FACTOR_PER_ATTRIBUTE_TYPE[attr.type];
      if (typeof sizeFactor !== "number") throw new Error('Program.bind: yet unsupported attribute type "'.concat(attr.type, '"'));
      var location = program.attributeLocations[attr.name];
      var gl = program.gl;
      if (location !== -1) {
        gl.enableVertexAttribArray(location);
        var stride = !this.isInstanced ? this.ATTRIBUTES_ITEMS_COUNT * Float32Array.BYTES_PER_ELEMENT : (setDivisor ? this.ATTRIBUTES_ITEMS_COUNT : getAttributesItemsCount(this.CONSTANT_ATTRIBUTES)) * Float32Array.BYTES_PER_ELEMENT;
        gl.vertexAttribPointer(location, attr.size, attr.type, attr.normalized || false, stride, offset);
        if (this.isInstanced && setDivisor) {
          if (gl instanceof WebGL2RenderingContext) {
            gl.vertexAttribDivisor(location, 1);
          } else {
            var ext = gl.getExtension("ANGLE_instanced_arrays");
            if (ext) ext.vertexAttribDivisorANGLE(location, 1);
          }
        }
      }
      return attr.size * sizeFactor;
    }
  }, {
    key: "unbindAttribute",
    value: function unbindAttribute(attr, program, unsetDivisor) {
      var location = program.attributeLocations[attr.name];
      var gl = program.gl;
      if (location !== -1) {
        gl.disableVertexAttribArray(location);
        if (this.isInstanced && unsetDivisor) {
          if (gl instanceof WebGL2RenderingContext) {
            gl.vertexAttribDivisor(location, 0);
          } else {
            var ext = gl.getExtension("ANGLE_instanced_arrays");
            if (ext) ext.vertexAttribDivisorANGLE(location, 0);
          }
        }
      }
    }
  }, {
    key: "reallocate",
    value: function reallocate(capacity) {
      if (capacity === this.capacity) return;
      this.capacity = capacity;
      this.verticesCount = this.VERTICES * capacity;
      this.array = new Float32Array(!this.isInstanced ? this.verticesCount * this.ATTRIBUTES_ITEMS_COUNT : this.capacity * this.ATTRIBUTES_ITEMS_COUNT);
    }
  }, {
    key: "hasNothingToRender",
    value: function hasNothingToRender() {
      return this.verticesCount === 0;
    }
  }, {
    key: "renderProgram",
    value: function renderProgram(params, programInfo) {
      var gl = programInfo.gl, program = programInfo.program;
      gl.enable(gl.BLEND);
      gl.useProgram(program);
      this.setUniforms(params, programInfo);
      this.drawWebGL(this.METHOD, programInfo);
    }
  }, {
    key: "render",
    value: function render(params) {
      if (this.hasNothingToRender()) return;
      if (this.pickProgram) {
        this.pickProgram.gl.viewport(0, 0, params.width * params.pixelRatio / params.downSizingRatio, params.height * params.pixelRatio / params.downSizingRatio);
        this.bindProgram(this.pickProgram);
        this.renderProgram(_objectSpread2(_objectSpread2({}, params), {}, {
          pixelRatio: params.pixelRatio / params.downSizingRatio
        }), this.pickProgram);
        this.unbindProgram(this.pickProgram);
      }
      this.normalProgram.gl.viewport(0, 0, params.width * params.pixelRatio, params.height * params.pixelRatio);
      this.bindProgram(this.normalProgram);
      this.renderProgram(params, this.normalProgram);
      this.unbindProgram(this.normalProgram);
    }
  }, {
    key: "drawWebGL",
    value: function drawWebGL(method, _ref) {
      var gl = _ref.gl, frameBuffer = _ref.frameBuffer;
      gl.bindFramebuffer(gl.FRAMEBUFFER, frameBuffer);
      if (!this.isInstanced) {
        gl.drawArrays(method, 0, this.verticesCount);
      } else {
        if (gl instanceof WebGL2RenderingContext) {
          gl.drawArraysInstanced(method, 0, this.VERTICES, this.capacity);
        } else {
          var ext = gl.getExtension("ANGLE_instanced_arrays");
          if (ext) ext.drawArraysInstancedANGLE(method, 0, this.VERTICES, this.capacity);
        }
      }
    }
  }]);
})();
var AbstractNodeProgram = (function(_AbstractProgram) {
  function AbstractNodeProgram2() {
    _classCallCheck(this, AbstractNodeProgram2);
    return _callSuper(this, AbstractNodeProgram2, arguments);
  }
  _inherits(AbstractNodeProgram2, _AbstractProgram);
  return _createClass(AbstractNodeProgram2);
})(AbstractProgram);
var NodeProgram = (function(_ref) {
  function NodeProgram2() {
    _classCallCheck(this, NodeProgram2);
    return _callSuper(this, NodeProgram2, arguments);
  }
  _inherits(NodeProgram2, _ref);
  return _createClass(NodeProgram2, [{
    key: "kill",
    value: function kill() {
      _superPropGet(NodeProgram2, "kill", this, 3)([]);
    }
  }, {
    key: "process",
    value: function process(nodeIndex, offset, data) {
      var i = offset * this.STRIDE;
      if (data.hidden) {
        for (var l = i + this.STRIDE; i < l; i++) {
          this.array[i] = 0;
        }
        return;
      }
      return this.processVisibleItem(indexToColor(nodeIndex), i, data);
    }
  }]);
})(Program);
function createNodeCompoundProgram(programClasses, drawLabel, drawHover) {
  return (function() {
    function NodeCompoundProgram(gl, pickingBuffer, renderer) {
      _classCallCheck(this, NodeCompoundProgram);
      _defineProperty(this, "drawLabel", drawLabel);
      _defineProperty(this, "drawHover", drawHover);
      this.programs = programClasses.map(function(Program2) {
        return new Program2(gl, pickingBuffer, renderer);
      });
    }
    return _createClass(NodeCompoundProgram, [{
      key: "reallocate",
      value: function reallocate(capacity) {
        this.programs.forEach(function(program) {
          return program.reallocate(capacity);
        });
      }
    }, {
      key: "process",
      value: function process(nodeIndex, offset, data) {
        this.programs.forEach(function(program) {
          return program.process(nodeIndex, offset, data);
        });
      }
    }, {
      key: "render",
      value: function render(params) {
        this.programs.forEach(function(program) {
          return program.render(params);
        });
      }
    }, {
      key: "kill",
      value: function kill() {
        this.programs.forEach(function(program) {
          return program.kill();
        });
      }
    }]);
  })();
}
var AbstractEdgeProgram = (function(_AbstractProgram) {
  function AbstractEdgeProgram2() {
    _classCallCheck(this, AbstractEdgeProgram2);
    return _callSuper(this, AbstractEdgeProgram2, arguments);
  }
  _inherits(AbstractEdgeProgram2, _AbstractProgram);
  return _createClass(AbstractEdgeProgram2);
})(AbstractProgram);
var EdgeProgram = (function(_ref) {
  function EdgeProgram2() {
    var _this;
    _classCallCheck(this, EdgeProgram2);
    for (var _len = arguments.length, args = new Array(_len), _key = 0; _key < _len; _key++) {
      args[_key] = arguments[_key];
    }
    _this = _callSuper(this, EdgeProgram2, [].concat(args));
    _defineProperty(_this, "drawLabel", void 0);
    return _this;
  }
  _inherits(EdgeProgram2, _ref);
  return _createClass(EdgeProgram2, [{
    key: "kill",
    value: function kill() {
      _superPropGet(EdgeProgram2, "kill", this, 3)([]);
    }
  }, {
    key: "process",
    value: function process(edgeIndex, offset, sourceData, targetData, data) {
      var i = offset * this.STRIDE;
      if (data.hidden || sourceData.hidden || targetData.hidden) {
        for (var l = i + this.STRIDE; i < l; i++) {
          this.array[i] = 0;
        }
        return;
      }
      return this.processVisibleItem(indexToColor(edgeIndex), i, sourceData, targetData, data);
    }
  }]);
})(Program);
function createEdgeCompoundProgram(programClasses, drawLabel) {
  return (function() {
    function EdgeCompoundProgram(gl, pickingBuffer, renderer) {
      _classCallCheck(this, EdgeCompoundProgram);
      _defineProperty(this, "drawLabel", drawLabel);
      this.programs = programClasses.map(function(Program2) {
        return new Program2(gl, pickingBuffer, renderer);
      });
    }
    return _createClass(EdgeCompoundProgram, [{
      key: "reallocate",
      value: function reallocate(capacity) {
        this.programs.forEach(function(program) {
          return program.reallocate(capacity);
        });
      }
    }, {
      key: "process",
      value: function process(edgeIndex, offset, sourceData, targetData, data) {
        this.programs.forEach(function(program) {
          return program.process(edgeIndex, offset, sourceData, targetData, data);
        });
      }
    }, {
      key: "render",
      value: function render(params) {
        this.programs.forEach(function(program) {
          return program.render(params);
        });
      }
    }, {
      key: "kill",
      value: function kill() {
        this.programs.forEach(function(program) {
          return program.kill();
        });
      }
    }]);
  })();
}
function drawStraightEdgeLabel(context, edgeData, sourceData, targetData, settings) {
  var size = settings.edgeLabelSize, font = settings.edgeLabelFont, weight = settings.edgeLabelWeight, color = settings.edgeLabelColor.attribute ? edgeData[settings.edgeLabelColor.attribute] || settings.edgeLabelColor.color || "#000" : settings.edgeLabelColor.color;
  var label = edgeData.label;
  if (!label) return;
  context.fillStyle = color;
  context.font = "".concat(weight, " ").concat(size, "px ").concat(font);
  var sSize = sourceData.size;
  var tSize = targetData.size;
  var sx = sourceData.x;
  var sy = sourceData.y;
  var tx = targetData.x;
  var ty = targetData.y;
  var cx = (sx + tx) / 2;
  var cy = (sy + ty) / 2;
  var dx = tx - sx;
  var dy = ty - sy;
  var d = Math.sqrt(dx * dx + dy * dy);
  if (d < sSize + tSize) return;
  sx += dx * sSize / d;
  sy += dy * sSize / d;
  tx -= dx * tSize / d;
  ty -= dy * tSize / d;
  cx = (sx + tx) / 2;
  cy = (sy + ty) / 2;
  dx = tx - sx;
  dy = ty - sy;
  d = Math.sqrt(dx * dx + dy * dy);
  var textLength = context.measureText(label).width;
  if (textLength > d) {
    var ellipsis = "…";
    label = label + ellipsis;
    textLength = context.measureText(label).width;
    while (textLength > d && label.length > 1) {
      label = label.slice(0, -2) + ellipsis;
      textLength = context.measureText(label).width;
    }
    if (label.length < 4) return;
  }
  var angle;
  if (dx > 0) {
    if (dy > 0) angle = Math.acos(dx / d);
    else angle = Math.asin(dy / d);
  } else {
    if (dy > 0) angle = Math.acos(dx / d) + Math.PI;
    else angle = Math.asin(dx / d) + Math.PI / 2;
  }
  context.save();
  context.translate(cx, cy);
  context.rotate(angle);
  context.fillText(label, -textLength / 2, edgeData.size / 2 + size);
  context.restore();
}
function drawDiscNodeLabel(context, data, settings) {
  if (!data.label) return;
  var size = settings.labelSize, font = settings.labelFont, weight = settings.labelWeight, color = settings.labelColor.attribute ? data[settings.labelColor.attribute] || settings.labelColor.color || "#000" : settings.labelColor.color;
  context.fillStyle = color;
  context.font = "".concat(weight, " ").concat(size, "px ").concat(font);
  context.fillText(data.label, data.x + data.size + 3, data.y + size / 3);
}
function drawDiscNodeHover(context, data, settings) {
  var size = settings.labelSize, font = settings.labelFont, weight = settings.labelWeight;
  context.font = "".concat(weight, " ").concat(size, "px ").concat(font);
  context.fillStyle = "#FFF";
  context.shadowOffsetX = 0;
  context.shadowOffsetY = 0;
  context.shadowBlur = 8;
  context.shadowColor = "#000";
  var PADDING = 2;
  if (typeof data.label === "string") {
    var textWidth = context.measureText(data.label).width, boxWidth = Math.round(textWidth + 5), boxHeight = Math.round(size + 2 * PADDING), radius = Math.max(data.size, size / 2) + PADDING;
    var angleRadian = Math.asin(boxHeight / 2 / radius);
    var xDeltaCoord = Math.sqrt(Math.abs(Math.pow(radius, 2) - Math.pow(boxHeight / 2, 2)));
    context.beginPath();
    context.moveTo(data.x + xDeltaCoord, data.y + boxHeight / 2);
    context.lineTo(data.x + radius + boxWidth, data.y + boxHeight / 2);
    context.lineTo(data.x + radius + boxWidth, data.y - boxHeight / 2);
    context.lineTo(data.x + xDeltaCoord, data.y - boxHeight / 2);
    context.arc(data.x, data.y, radius, angleRadian, -angleRadian);
    context.closePath();
    context.fill();
  } else {
    context.beginPath();
    context.arc(data.x, data.y, data.size + PADDING, 0, Math.PI * 2);
    context.closePath();
    context.fill();
  }
  context.shadowOffsetX = 0;
  context.shadowOffsetY = 0;
  context.shadowBlur = 0;
  drawDiscNodeLabel(context, data, settings);
}
var SHADER_SOURCE$6 = (
  /*glsl*/
  "\nprecision highp float;\n\nvarying vec4 v_color;\nvarying vec2 v_diffVector;\nvarying float v_radius;\n\nuniform float u_correctionRatio;\n\nconst vec4 transparent = vec4(0.0, 0.0, 0.0, 0.0);\n\nvoid main(void) {\n  float border = u_correctionRatio * 2.0;\n  float dist = length(v_diffVector) - v_radius + border;\n\n  // No antialiasing for picking mode:\n  #ifdef PICKING_MODE\n  if (dist > border)\n    gl_FragColor = transparent;\n  else\n    gl_FragColor = v_color;\n\n  #else\n  float t = 0.0;\n  if (dist > border)\n    t = 1.0;\n  else if (dist > 0.0)\n    t = dist / border;\n\n  gl_FragColor = mix(v_color, transparent, t);\n  #endif\n}\n"
);
var FRAGMENT_SHADER_SOURCE$2 = SHADER_SOURCE$6;
var SHADER_SOURCE$5 = (
  /*glsl*/
  "\nattribute vec4 a_id;\nattribute vec4 a_color;\nattribute vec2 a_position;\nattribute float a_size;\nattribute float a_angle;\n\nuniform mat3 u_matrix;\nuniform float u_sizeRatio;\nuniform float u_correctionRatio;\n\nvarying vec4 v_color;\nvarying vec2 v_diffVector;\nvarying float v_radius;\nvarying float v_border;\n\nconst float bias = 255.0 / 254.0;\n\nvoid main() {\n  float size = a_size * u_correctionRatio / u_sizeRatio * 4.0;\n  vec2 diffVector = size * vec2(cos(a_angle), sin(a_angle));\n  vec2 position = a_position + diffVector;\n  gl_Position = vec4(\n    (u_matrix * vec3(position, 1)).xy,\n    0,\n    1\n  );\n\n  v_diffVector = diffVector;\n  v_radius = size / 2.0;\n\n  #ifdef PICKING_MODE\n  // For picking mode, we use the ID as the color:\n  v_color = a_id;\n  #else\n  // For normal mode, we use the color:\n  v_color = a_color;\n  #endif\n\n  v_color.a *= bias;\n}\n"
);
var VERTEX_SHADER_SOURCE$3 = SHADER_SOURCE$5;
var _WebGLRenderingContex$3 = WebGLRenderingContext;
var UNSIGNED_BYTE$3 = _WebGLRenderingContex$3.UNSIGNED_BYTE;
var FLOAT$3 = _WebGLRenderingContex$3.FLOAT;
var UNIFORMS$3 = ["u_sizeRatio", "u_correctionRatio", "u_matrix"];
var NodeCircleProgram = (function(_NodeProgram) {
  function NodeCircleProgram2() {
    _classCallCheck(this, NodeCircleProgram2);
    return _callSuper(this, NodeCircleProgram2, arguments);
  }
  _inherits(NodeCircleProgram2, _NodeProgram);
  return _createClass(NodeCircleProgram2, [{
    key: "getDefinition",
    value: function getDefinition() {
      return {
        VERTICES: 3,
        VERTEX_SHADER_SOURCE: VERTEX_SHADER_SOURCE$3,
        FRAGMENT_SHADER_SOURCE: FRAGMENT_SHADER_SOURCE$2,
        METHOD: WebGLRenderingContext.TRIANGLES,
        UNIFORMS: UNIFORMS$3,
        ATTRIBUTES: [{
          name: "a_position",
          size: 2,
          type: FLOAT$3
        }, {
          name: "a_size",
          size: 1,
          type: FLOAT$3
        }, {
          name: "a_color",
          size: 4,
          type: UNSIGNED_BYTE$3,
          normalized: true
        }, {
          name: "a_id",
          size: 4,
          type: UNSIGNED_BYTE$3,
          normalized: true
        }],
        CONSTANT_ATTRIBUTES: [{
          name: "a_angle",
          size: 1,
          type: FLOAT$3
        }],
        CONSTANT_DATA: [[NodeCircleProgram2.ANGLE_1], [NodeCircleProgram2.ANGLE_2], [NodeCircleProgram2.ANGLE_3]]
      };
    }
  }, {
    key: "processVisibleItem",
    value: function processVisibleItem(nodeIndex, startIndex, data) {
      var array = this.array;
      var color = floatColor(data.color);
      array[startIndex++] = data.x;
      array[startIndex++] = data.y;
      array[startIndex++] = data.size;
      array[startIndex++] = color;
      array[startIndex++] = nodeIndex;
    }
  }, {
    key: "setUniforms",
    value: function setUniforms(params, _ref) {
      var gl = _ref.gl, uniformLocations = _ref.uniformLocations;
      var u_sizeRatio = uniformLocations.u_sizeRatio, u_correctionRatio = uniformLocations.u_correctionRatio, u_matrix = uniformLocations.u_matrix;
      gl.uniform1f(u_correctionRatio, params.correctionRatio);
      gl.uniform1f(u_sizeRatio, params.sizeRatio);
      gl.uniformMatrix3fv(u_matrix, false, params.matrix);
    }
  }]);
})(NodeProgram);
_defineProperty(NodeCircleProgram, "ANGLE_1", 0);
_defineProperty(NodeCircleProgram, "ANGLE_2", 2 * Math.PI / 3);
_defineProperty(NodeCircleProgram, "ANGLE_3", 4 * Math.PI / 3);
var SHADER_SOURCE$4 = (
  /*glsl*/
  "\nprecision mediump float;\n\nvarying vec4 v_color;\n\nvoid main(void) {\n  gl_FragColor = v_color;\n}\n"
);
var FRAGMENT_SHADER_SOURCE$1 = SHADER_SOURCE$4;
var SHADER_SOURCE$3 = (
  /*glsl*/
  "\nattribute vec2 a_position;\nattribute vec2 a_normal;\nattribute float a_radius;\nattribute vec3 a_barycentric;\n\n#ifdef PICKING_MODE\nattribute vec4 a_id;\n#else\nattribute vec4 a_color;\n#endif\n\nuniform mat3 u_matrix;\nuniform float u_sizeRatio;\nuniform float u_correctionRatio;\nuniform float u_minEdgeThickness;\nuniform float u_lengthToThicknessRatio;\nuniform float u_widenessToThicknessRatio;\n\nvarying vec4 v_color;\n\nconst float bias = 255.0 / 254.0;\n\nvoid main() {\n  float minThickness = u_minEdgeThickness;\n\n  float normalLength = length(a_normal);\n  vec2 unitNormal = a_normal / normalLength;\n\n  // These first computations are taken from edge.vert.glsl and\n  // edge.clamped.vert.glsl. Please read it to get better comments on what's\n  // happening:\n  float pixelsThickness = max(normalLength / u_sizeRatio, minThickness);\n  float webGLThickness = pixelsThickness * u_correctionRatio;\n  float webGLNodeRadius = a_radius * 2.0 * u_correctionRatio / u_sizeRatio;\n  float webGLArrowHeadLength = webGLThickness * u_lengthToThicknessRatio * 2.0;\n  float webGLArrowHeadThickness = webGLThickness * u_widenessToThicknessRatio;\n\n  float da = a_barycentric.x;\n  float db = a_barycentric.y;\n  float dc = a_barycentric.z;\n\n  vec2 delta = vec2(\n      da * (webGLNodeRadius * unitNormal.y)\n    + db * ((webGLNodeRadius + webGLArrowHeadLength) * unitNormal.y + webGLArrowHeadThickness * unitNormal.x)\n    + dc * ((webGLNodeRadius + webGLArrowHeadLength) * unitNormal.y - webGLArrowHeadThickness * unitNormal.x),\n\n      da * (-webGLNodeRadius * unitNormal.x)\n    + db * (-(webGLNodeRadius + webGLArrowHeadLength) * unitNormal.x + webGLArrowHeadThickness * unitNormal.y)\n    + dc * (-(webGLNodeRadius + webGLArrowHeadLength) * unitNormal.x - webGLArrowHeadThickness * unitNormal.y)\n  );\n\n  vec2 position = (u_matrix * vec3(a_position + delta, 1)).xy;\n\n  gl_Position = vec4(position, 0, 1);\n\n  #ifdef PICKING_MODE\n  // For picking mode, we use the ID as the color:\n  v_color = a_id;\n  #else\n  // For normal mode, we use the color:\n  v_color = a_color;\n  #endif\n\n  v_color.a *= bias;\n}\n"
);
var VERTEX_SHADER_SOURCE$2 = SHADER_SOURCE$3;
var _WebGLRenderingContex$2 = WebGLRenderingContext;
var UNSIGNED_BYTE$2 = _WebGLRenderingContex$2.UNSIGNED_BYTE;
var FLOAT$2 = _WebGLRenderingContex$2.FLOAT;
var UNIFORMS$2 = ["u_matrix", "u_sizeRatio", "u_correctionRatio", "u_minEdgeThickness", "u_lengthToThicknessRatio", "u_widenessToThicknessRatio"];
var DEFAULT_EDGE_ARROW_HEAD_PROGRAM_OPTIONS = {
  extremity: "target",
  lengthToThicknessRatio: 2.5,
  widenessToThicknessRatio: 2
};
function createEdgeArrowHeadProgram(inputOptions) {
  var options = _objectSpread2(_objectSpread2({}, DEFAULT_EDGE_ARROW_HEAD_PROGRAM_OPTIONS), inputOptions || {});
  return (function(_EdgeProgram) {
    function EdgeArrowHeadProgram2() {
      _classCallCheck(this, EdgeArrowHeadProgram2);
      return _callSuper(this, EdgeArrowHeadProgram2, arguments);
    }
    _inherits(EdgeArrowHeadProgram2, _EdgeProgram);
    return _createClass(EdgeArrowHeadProgram2, [{
      key: "getDefinition",
      value: function getDefinition() {
        return {
          VERTICES: 3,
          VERTEX_SHADER_SOURCE: VERTEX_SHADER_SOURCE$2,
          FRAGMENT_SHADER_SOURCE: FRAGMENT_SHADER_SOURCE$1,
          METHOD: WebGLRenderingContext.TRIANGLES,
          UNIFORMS: UNIFORMS$2,
          ATTRIBUTES: [{
            name: "a_position",
            size: 2,
            type: FLOAT$2
          }, {
            name: "a_normal",
            size: 2,
            type: FLOAT$2
          }, {
            name: "a_radius",
            size: 1,
            type: FLOAT$2
          }, {
            name: "a_color",
            size: 4,
            type: UNSIGNED_BYTE$2,
            normalized: true
          }, {
            name: "a_id",
            size: 4,
            type: UNSIGNED_BYTE$2,
            normalized: true
          }],
          CONSTANT_ATTRIBUTES: [{
            name: "a_barycentric",
            size: 3,
            type: FLOAT$2
          }],
          CONSTANT_DATA: [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        };
      }
    }, {
      key: "processVisibleItem",
      value: function processVisibleItem(edgeIndex, startIndex, sourceData, targetData, data) {
        if (options.extremity === "source") {
          var _ref = [targetData, sourceData];
          sourceData = _ref[0];
          targetData = _ref[1];
        }
        var thickness = data.size || 1;
        var radius = targetData.size || 1;
        var x1 = sourceData.x;
        var y1 = sourceData.y;
        var x2 = targetData.x;
        var y2 = targetData.y;
        var color = floatColor(data.color);
        var dx = x2 - x1;
        var dy = y2 - y1;
        var len = dx * dx + dy * dy;
        var n1 = 0;
        var n2 = 0;
        if (len) {
          len = 1 / Math.sqrt(len);
          n1 = -dy * len * thickness;
          n2 = dx * len * thickness;
        }
        var array = this.array;
        array[startIndex++] = x2;
        array[startIndex++] = y2;
        array[startIndex++] = -n1;
        array[startIndex++] = -n2;
        array[startIndex++] = radius;
        array[startIndex++] = color;
        array[startIndex++] = edgeIndex;
      }
    }, {
      key: "setUniforms",
      value: function setUniforms(params, _ref2) {
        var gl = _ref2.gl, uniformLocations = _ref2.uniformLocations;
        var u_matrix = uniformLocations.u_matrix, u_sizeRatio = uniformLocations.u_sizeRatio, u_correctionRatio = uniformLocations.u_correctionRatio, u_minEdgeThickness = uniformLocations.u_minEdgeThickness, u_lengthToThicknessRatio = uniformLocations.u_lengthToThicknessRatio, u_widenessToThicknessRatio = uniformLocations.u_widenessToThicknessRatio;
        gl.uniformMatrix3fv(u_matrix, false, params.matrix);
        gl.uniform1f(u_sizeRatio, params.sizeRatio);
        gl.uniform1f(u_correctionRatio, params.correctionRatio);
        gl.uniform1f(u_minEdgeThickness, params.minEdgeThickness);
        gl.uniform1f(u_lengthToThicknessRatio, options.lengthToThicknessRatio);
        gl.uniform1f(u_widenessToThicknessRatio, options.widenessToThicknessRatio);
      }
    }]);
  })(EdgeProgram);
}
var EdgeArrowHeadProgram = createEdgeArrowHeadProgram();
var EdgeArrowHeadProgram$1 = EdgeArrowHeadProgram;
var SHADER_SOURCE$2 = (
  /*glsl*/
  "\nprecision mediump float;\n\nvarying vec4 v_color;\nvarying vec2 v_normal;\nvarying float v_thickness;\nvarying float v_feather;\n\nconst vec4 transparent = vec4(0.0, 0.0, 0.0, 0.0);\n\nvoid main(void) {\n  // We only handle antialiasing for normal mode:\n  #ifdef PICKING_MODE\n  gl_FragColor = v_color;\n  #else\n  float dist = length(v_normal) * v_thickness;\n\n  float t = smoothstep(\n    v_thickness - v_feather,\n    v_thickness,\n    dist\n  );\n\n  gl_FragColor = mix(v_color, transparent, t);\n  #endif\n}\n"
);
var FRAGMENT_SHADER_SOURCE = SHADER_SOURCE$2;
var SHADER_SOURCE$1 = (
  /*glsl*/
  "\nattribute vec4 a_id;\nattribute vec4 a_color;\nattribute vec2 a_normal;\nattribute float a_normalCoef;\nattribute vec2 a_positionStart;\nattribute vec2 a_positionEnd;\nattribute float a_positionCoef;\nattribute float a_radius;\nattribute float a_radiusCoef;\n\nuniform mat3 u_matrix;\nuniform float u_zoomRatio;\nuniform float u_sizeRatio;\nuniform float u_pixelRatio;\nuniform float u_correctionRatio;\nuniform float u_minEdgeThickness;\nuniform float u_lengthToThicknessRatio;\nuniform float u_feather;\n\nvarying vec4 v_color;\nvarying vec2 v_normal;\nvarying float v_thickness;\nvarying float v_feather;\n\nconst float bias = 255.0 / 254.0;\n\nvoid main() {\n  float minThickness = u_minEdgeThickness;\n\n  float radius = a_radius * a_radiusCoef;\n  vec2 normal = a_normal * a_normalCoef;\n  vec2 position = a_positionStart * (1.0 - a_positionCoef) + a_positionEnd * a_positionCoef;\n\n  float normalLength = length(normal);\n  vec2 unitNormal = normal / normalLength;\n\n  // These first computations are taken from edge.vert.glsl. Please read it to\n  // get better comments on what's happening:\n  float pixelsThickness = max(normalLength, minThickness * u_sizeRatio);\n  float webGLThickness = pixelsThickness * u_correctionRatio / u_sizeRatio;\n\n  // Here, we move the point to leave space for the arrow head:\n  float direction = sign(radius);\n  float webGLNodeRadius = direction * radius * 2.0 * u_correctionRatio / u_sizeRatio;\n  float webGLArrowHeadLength = webGLThickness * u_lengthToThicknessRatio * 2.0;\n\n  vec2 compensationVector = vec2(-direction * unitNormal.y, direction * unitNormal.x) * (webGLNodeRadius + webGLArrowHeadLength);\n\n  // Here is the proper position of the vertex\n  gl_Position = vec4((u_matrix * vec3(position + unitNormal * webGLThickness + compensationVector, 1)).xy, 0, 1);\n\n  v_thickness = webGLThickness / u_zoomRatio;\n\n  v_normal = unitNormal;\n\n  v_feather = u_feather * u_correctionRatio / u_zoomRatio / u_pixelRatio * 2.0;\n\n  #ifdef PICKING_MODE\n  // For picking mode, we use the ID as the color:\n  v_color = a_id;\n  #else\n  // For normal mode, we use the color:\n  v_color = a_color;\n  #endif\n\n  v_color.a *= bias;\n}\n"
);
var VERTEX_SHADER_SOURCE$1 = SHADER_SOURCE$1;
var _WebGLRenderingContex$1 = WebGLRenderingContext;
var UNSIGNED_BYTE$1 = _WebGLRenderingContex$1.UNSIGNED_BYTE;
var FLOAT$1 = _WebGLRenderingContex$1.FLOAT;
var UNIFORMS$1 = ["u_matrix", "u_zoomRatio", "u_sizeRatio", "u_correctionRatio", "u_pixelRatio", "u_feather", "u_minEdgeThickness", "u_lengthToThicknessRatio"];
var DEFAULT_EDGE_CLAMPED_PROGRAM_OPTIONS = {
  lengthToThicknessRatio: DEFAULT_EDGE_ARROW_HEAD_PROGRAM_OPTIONS.lengthToThicknessRatio
};
function createEdgeClampedProgram(inputOptions) {
  var options = _objectSpread2(_objectSpread2({}, DEFAULT_EDGE_CLAMPED_PROGRAM_OPTIONS), inputOptions || {});
  return (function(_EdgeProgram) {
    function EdgeClampedProgram2() {
      _classCallCheck(this, EdgeClampedProgram2);
      return _callSuper(this, EdgeClampedProgram2, arguments);
    }
    _inherits(EdgeClampedProgram2, _EdgeProgram);
    return _createClass(EdgeClampedProgram2, [{
      key: "getDefinition",
      value: function getDefinition() {
        return {
          VERTICES: 6,
          VERTEX_SHADER_SOURCE: VERTEX_SHADER_SOURCE$1,
          FRAGMENT_SHADER_SOURCE,
          METHOD: WebGLRenderingContext.TRIANGLES,
          UNIFORMS: UNIFORMS$1,
          ATTRIBUTES: [{
            name: "a_positionStart",
            size: 2,
            type: FLOAT$1
          }, {
            name: "a_positionEnd",
            size: 2,
            type: FLOAT$1
          }, {
            name: "a_normal",
            size: 2,
            type: FLOAT$1
          }, {
            name: "a_color",
            size: 4,
            type: UNSIGNED_BYTE$1,
            normalized: true
          }, {
            name: "a_id",
            size: 4,
            type: UNSIGNED_BYTE$1,
            normalized: true
          }, {
            name: "a_radius",
            size: 1,
            type: FLOAT$1
          }],
          CONSTANT_ATTRIBUTES: [
            // If 0, then position will be a_positionStart
            // If 1, then position will be a_positionEnd
            {
              name: "a_positionCoef",
              size: 1,
              type: FLOAT$1
            },
            {
              name: "a_normalCoef",
              size: 1,
              type: FLOAT$1
            },
            {
              name: "a_radiusCoef",
              size: 1,
              type: FLOAT$1
            }
          ],
          CONSTANT_DATA: [[0, 1, 0], [0, -1, 0], [1, 1, 1], [1, 1, 1], [0, -1, 0], [1, -1, -1]]
        };
      }
    }, {
      key: "processVisibleItem",
      value: function processVisibleItem(edgeIndex, startIndex, sourceData, targetData, data) {
        var thickness = data.size || 1;
        var x1 = sourceData.x;
        var y1 = sourceData.y;
        var x2 = targetData.x;
        var y2 = targetData.y;
        var color = floatColor(data.color);
        var dx = x2 - x1;
        var dy = y2 - y1;
        var radius = targetData.size || 1;
        var len = dx * dx + dy * dy;
        var n1 = 0;
        var n2 = 0;
        if (len) {
          len = 1 / Math.sqrt(len);
          n1 = -dy * len * thickness;
          n2 = dx * len * thickness;
        }
        var array = this.array;
        array[startIndex++] = x1;
        array[startIndex++] = y1;
        array[startIndex++] = x2;
        array[startIndex++] = y2;
        array[startIndex++] = n1;
        array[startIndex++] = n2;
        array[startIndex++] = color;
        array[startIndex++] = edgeIndex;
        array[startIndex++] = radius;
      }
    }, {
      key: "setUniforms",
      value: function setUniforms(params, _ref) {
        var gl = _ref.gl, uniformLocations = _ref.uniformLocations;
        var u_matrix = uniformLocations.u_matrix, u_zoomRatio = uniformLocations.u_zoomRatio, u_feather = uniformLocations.u_feather, u_pixelRatio = uniformLocations.u_pixelRatio, u_correctionRatio = uniformLocations.u_correctionRatio, u_sizeRatio = uniformLocations.u_sizeRatio, u_minEdgeThickness = uniformLocations.u_minEdgeThickness, u_lengthToThicknessRatio = uniformLocations.u_lengthToThicknessRatio;
        gl.uniformMatrix3fv(u_matrix, false, params.matrix);
        gl.uniform1f(u_zoomRatio, params.zoomRatio);
        gl.uniform1f(u_sizeRatio, params.sizeRatio);
        gl.uniform1f(u_correctionRatio, params.correctionRatio);
        gl.uniform1f(u_pixelRatio, params.pixelRatio);
        gl.uniform1f(u_feather, params.antiAliasingFeather);
        gl.uniform1f(u_minEdgeThickness, params.minEdgeThickness);
        gl.uniform1f(u_lengthToThicknessRatio, options.lengthToThicknessRatio);
      }
    }]);
  })(EdgeProgram);
}
var EdgeClampedProgram = createEdgeClampedProgram();
var EdgeClampedProgram$1 = EdgeClampedProgram;
function createEdgeArrowProgram(inputOptions) {
  return createEdgeCompoundProgram([createEdgeClampedProgram(inputOptions), createEdgeArrowHeadProgram(inputOptions)]);
}
var EdgeArrowProgram = createEdgeArrowProgram();
var EdgeArrowProgram$1 = EdgeArrowProgram;
var SHADER_SOURCE = (
  /*glsl*/
  `
attribute vec4 a_id;
attribute vec4 a_color;
attribute vec2 a_normal;
attribute float a_normalCoef;
attribute vec2 a_positionStart;
attribute vec2 a_positionEnd;
attribute float a_positionCoef;

uniform mat3 u_matrix;
uniform float u_sizeRatio;
uniform float u_zoomRatio;
uniform float u_pixelRatio;
uniform float u_correctionRatio;
uniform float u_minEdgeThickness;
uniform float u_feather;

varying vec4 v_color;
varying vec2 v_normal;
varying float v_thickness;
varying float v_feather;

const float bias = 255.0 / 254.0;

void main() {
  float minThickness = u_minEdgeThickness;

  vec2 normal = a_normal * a_normalCoef;
  vec2 position = a_positionStart * (1.0 - a_positionCoef) + a_positionEnd * a_positionCoef;

  float normalLength = length(normal);
  vec2 unitNormal = normal / normalLength;

  // We require edges to be at least "minThickness" pixels thick *on screen*
  // (so we need to compensate the size ratio):
  float pixelsThickness = max(normalLength, minThickness * u_sizeRatio);

  // Then, we need to retrieve the normalized thickness of the edge in the WebGL
  // referential (in a ([0, 1], [0, 1]) space), using our "magic" correction
  // ratio:
  float webGLThickness = pixelsThickness * u_correctionRatio / u_sizeRatio;

  // Here is the proper position of the vertex
  gl_Position = vec4((u_matrix * vec3(position + unitNormal * webGLThickness, 1)).xy, 0, 1);

  // For the fragment shader though, we need a thickness that takes the "magic"
  // correction ratio into account (as in webGLThickness), but so that the
  // antialiasing effect does not depend on the zoom level. So here's yet
  // another thickness version:
  v_thickness = webGLThickness / u_zoomRatio;

  v_normal = unitNormal;

  v_feather = u_feather * u_correctionRatio / u_zoomRatio / u_pixelRatio * 2.0;

  #ifdef PICKING_MODE
  // For picking mode, we use the ID as the color:
  v_color = a_id;
  #else
  // For normal mode, we use the color:
  v_color = a_color;
  #endif

  v_color.a *= bias;
}
`
);
var VERTEX_SHADER_SOURCE = SHADER_SOURCE;
var _WebGLRenderingContex = WebGLRenderingContext;
var UNSIGNED_BYTE = _WebGLRenderingContex.UNSIGNED_BYTE;
var FLOAT = _WebGLRenderingContex.FLOAT;
var UNIFORMS = ["u_matrix", "u_zoomRatio", "u_sizeRatio", "u_correctionRatio", "u_pixelRatio", "u_feather", "u_minEdgeThickness"];
var EdgeRectangleProgram = (function(_EdgeProgram) {
  function EdgeRectangleProgram2() {
    _classCallCheck(this, EdgeRectangleProgram2);
    return _callSuper(this, EdgeRectangleProgram2, arguments);
  }
  _inherits(EdgeRectangleProgram2, _EdgeProgram);
  return _createClass(EdgeRectangleProgram2, [{
    key: "getDefinition",
    value: function getDefinition() {
      return {
        VERTICES: 6,
        VERTEX_SHADER_SOURCE,
        FRAGMENT_SHADER_SOURCE,
        METHOD: WebGLRenderingContext.TRIANGLES,
        UNIFORMS,
        ATTRIBUTES: [{
          name: "a_positionStart",
          size: 2,
          type: FLOAT
        }, {
          name: "a_positionEnd",
          size: 2,
          type: FLOAT
        }, {
          name: "a_normal",
          size: 2,
          type: FLOAT
        }, {
          name: "a_color",
          size: 4,
          type: UNSIGNED_BYTE,
          normalized: true
        }, {
          name: "a_id",
          size: 4,
          type: UNSIGNED_BYTE,
          normalized: true
        }],
        CONSTANT_ATTRIBUTES: [
          // If 0, then position will be a_positionStart
          // If 2, then position will be a_positionEnd
          {
            name: "a_positionCoef",
            size: 1,
            type: FLOAT
          },
          {
            name: "a_normalCoef",
            size: 1,
            type: FLOAT
          }
        ],
        CONSTANT_DATA: [[0, 1], [0, -1], [1, 1], [1, 1], [0, -1], [1, -1]]
      };
    }
  }, {
    key: "processVisibleItem",
    value: function processVisibleItem(edgeIndex, startIndex, sourceData, targetData, data) {
      var thickness = data.size || 1;
      var x1 = sourceData.x;
      var y1 = sourceData.y;
      var x2 = targetData.x;
      var y2 = targetData.y;
      var color = floatColor(data.color);
      var dx = x2 - x1;
      var dy = y2 - y1;
      var len = dx * dx + dy * dy;
      var n1 = 0;
      var n2 = 0;
      if (len) {
        len = 1 / Math.sqrt(len);
        n1 = -dy * len * thickness;
        n2 = dx * len * thickness;
      }
      var array = this.array;
      array[startIndex++] = x1;
      array[startIndex++] = y1;
      array[startIndex++] = x2;
      array[startIndex++] = y2;
      array[startIndex++] = n1;
      array[startIndex++] = n2;
      array[startIndex++] = color;
      array[startIndex++] = edgeIndex;
    }
  }, {
    key: "setUniforms",
    value: function setUniforms(params, _ref) {
      var gl = _ref.gl, uniformLocations = _ref.uniformLocations;
      var u_matrix = uniformLocations.u_matrix, u_zoomRatio = uniformLocations.u_zoomRatio, u_feather = uniformLocations.u_feather, u_pixelRatio = uniformLocations.u_pixelRatio, u_correctionRatio = uniformLocations.u_correctionRatio, u_sizeRatio = uniformLocations.u_sizeRatio, u_minEdgeThickness = uniformLocations.u_minEdgeThickness;
      gl.uniformMatrix3fv(u_matrix, false, params.matrix);
      gl.uniform1f(u_zoomRatio, params.zoomRatio);
      gl.uniform1f(u_sizeRatio, params.sizeRatio);
      gl.uniform1f(u_correctionRatio, params.correctionRatio);
      gl.uniform1f(u_pixelRatio, params.pixelRatio);
      gl.uniform1f(u_feather, params.antiAliasingFeather);
      gl.uniform1f(u_minEdgeThickness, params.minEdgeThickness);
    }
  }]);
})(EdgeProgram);

export {
  _toPropertyKey,
  _classCallCheck,
  _createClass,
  _callSuper,
  _inherits,
  _arrayLikeToArray,
  _unsupportedIterableToArray,
  _slicedToArray,
  floatColor,
  colorToIndex,
  getPixelColor,
  _defineProperty,
  _objectSpread2,
  getAttributeItemsCount,
  getAttributesItemsCount,
  loadVertexShader,
  loadFragmentShader,
  loadProgram,
  killProgram,
  numberToGLSLFloat,
  AbstractProgram,
  Program,
  AbstractNodeProgram,
  NodeProgram,
  createNodeCompoundProgram,
  AbstractEdgeProgram,
  EdgeProgram,
  createEdgeCompoundProgram,
  drawStraightEdgeLabel,
  drawDiscNodeLabel,
  drawDiscNodeHover,
  NodeCircleProgram,
  DEFAULT_EDGE_ARROW_HEAD_PROGRAM_OPTIONS,
  createEdgeArrowHeadProgram,
  EdgeArrowHeadProgram$1,
  FRAGMENT_SHADER_SOURCE,
  DEFAULT_EDGE_CLAMPED_PROGRAM_OPTIONS,
  createEdgeClampedProgram,
  EdgeClampedProgram$1,
  createEdgeArrowProgram,
  EdgeArrowProgram$1,
  EdgeRectangleProgram
};
//# sourceMappingURL=chunk-NTXYWN7O.js.map
