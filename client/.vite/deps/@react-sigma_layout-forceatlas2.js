import {
  j,
  v
} from "./chunk-SRZRMQHD.js";
import {
  require_is_graph
} from "./chunk-XHBEL7IJ.js";
import "./chunk-NTXYWN7O.js";
import {
  require_react
} from "./chunk-QYXY6RWP.js";
import "./chunk-LQBAZ7HZ.js";
import "./chunk-E6PT4EQ2.js";
import {
  __commonJS,
  __toESM
} from "./chunk-5WRI5ZAA.js";

// node_modules/graphology-utils/getters.js
var require_getters = __commonJS({
  "node_modules/graphology-utils/getters.js"(exports) {
    function coerceWeight(value) {
      if (typeof value !== "number" || isNaN(value)) return 1;
      return value;
    }
    function createNodeValueGetter(nameOrFunction, defaultValue) {
      var getter = {};
      var coerceToDefault = function(v2) {
        if (typeof v2 === "undefined") return defaultValue;
        return v2;
      };
      if (typeof defaultValue === "function") coerceToDefault = defaultValue;
      var get = function(attributes) {
        return coerceToDefault(attributes[nameOrFunction]);
      };
      var returnDefault = function() {
        return coerceToDefault(void 0);
      };
      if (typeof nameOrFunction === "string") {
        getter.fromAttributes = get;
        getter.fromGraph = function(graph, node) {
          return get(graph.getNodeAttributes(node));
        };
        getter.fromEntry = function(node, attributes) {
          return get(attributes);
        };
      } else if (typeof nameOrFunction === "function") {
        getter.fromAttributes = function() {
          throw new Error(
            "graphology-utils/getters/createNodeValueGetter: irrelevant usage."
          );
        };
        getter.fromGraph = function(graph, node) {
          return coerceToDefault(
            nameOrFunction(node, graph.getNodeAttributes(node))
          );
        };
        getter.fromEntry = function(node, attributes) {
          return coerceToDefault(nameOrFunction(node, attributes));
        };
      } else {
        getter.fromAttributes = returnDefault;
        getter.fromGraph = returnDefault;
        getter.fromEntry = returnDefault;
      }
      return getter;
    }
    function createEdgeValueGetter(nameOrFunction, defaultValue) {
      var getter = {};
      var coerceToDefault = function(v2) {
        if (typeof v2 === "undefined") return defaultValue;
        return v2;
      };
      if (typeof defaultValue === "function") coerceToDefault = defaultValue;
      var get = function(attributes) {
        return coerceToDefault(attributes[nameOrFunction]);
      };
      var returnDefault = function() {
        return coerceToDefault(void 0);
      };
      if (typeof nameOrFunction === "string") {
        getter.fromAttributes = get;
        getter.fromGraph = function(graph, edge) {
          return get(graph.getEdgeAttributes(edge));
        };
        getter.fromEntry = function(edge, attributes) {
          return get(attributes);
        };
        getter.fromPartialEntry = getter.fromEntry;
        getter.fromMinimalEntry = getter.fromEntry;
      } else if (typeof nameOrFunction === "function") {
        getter.fromAttributes = function() {
          throw new Error(
            "graphology-utils/getters/createEdgeValueGetter: irrelevant usage."
          );
        };
        getter.fromGraph = function(graph, edge) {
          var extremities = graph.extremities(edge);
          return coerceToDefault(
            nameOrFunction(
              edge,
              graph.getEdgeAttributes(edge),
              extremities[0],
              extremities[1],
              graph.getNodeAttributes(extremities[0]),
              graph.getNodeAttributes(extremities[1]),
              graph.isUndirected(edge)
            )
          );
        };
        getter.fromEntry = function(e2, a3, s3, t, sa, ta, u2) {
          return coerceToDefault(nameOrFunction(e2, a3, s3, t, sa, ta, u2));
        };
        getter.fromPartialEntry = function(e2, a3, s3, t) {
          return coerceToDefault(nameOrFunction(e2, a3, s3, t));
        };
        getter.fromMinimalEntry = function(e2, a3) {
          return coerceToDefault(nameOrFunction(e2, a3));
        };
      } else {
        getter.fromAttributes = returnDefault;
        getter.fromGraph = returnDefault;
        getter.fromEntry = returnDefault;
        getter.fromMinimalEntry = returnDefault;
      }
      return getter;
    }
    exports.createNodeValueGetter = createNodeValueGetter;
    exports.createEdgeValueGetter = createEdgeValueGetter;
    exports.createEdgeWeightGetter = function(name) {
      return createEdgeValueGetter(name, coerceWeight);
    };
  }
});

// node_modules/graphology-layout-forceatlas2/iterate.js
var require_iterate = __commonJS({
  "node_modules/graphology-layout-forceatlas2/iterate.js"(exports, module) {
    var NODE_X = 0;
    var NODE_Y = 1;
    var NODE_DX = 2;
    var NODE_DY = 3;
    var NODE_OLD_DX = 4;
    var NODE_OLD_DY = 5;
    var NODE_MASS = 6;
    var NODE_CONVERGENCE = 7;
    var NODE_SIZE = 8;
    var NODE_FIXED = 9;
    var EDGE_SOURCE = 0;
    var EDGE_TARGET = 1;
    var EDGE_WEIGHT = 2;
    var REGION_NODE = 0;
    var REGION_CENTER_X = 1;
    var REGION_CENTER_Y = 2;
    var REGION_SIZE = 3;
    var REGION_NEXT_SIBLING = 4;
    var REGION_FIRST_CHILD = 5;
    var REGION_MASS = 6;
    var REGION_MASS_CENTER_X = 7;
    var REGION_MASS_CENTER_Y = 8;
    var SUBDIVISION_ATTEMPTS = 3;
    var PPN = 10;
    var PPE = 3;
    var PPR = 9;
    var MAX_FORCE = 10;
    module.exports = function iterate(options, NodeMatrix, EdgeMatrix) {
      var l3, r2, n3, n1, n22, rn, e2, w, g2, s3;
      var order = NodeMatrix.length, size = EdgeMatrix.length;
      var adjustSizes = options.adjustSizes;
      var thetaSquared = options.barnesHutTheta * options.barnesHutTheta;
      var outboundAttCompensation, coefficient, xDist, yDist, ewc, distance, factor;
      var RegionMatrix = [];
      for (n3 = 0; n3 < order; n3 += PPN) {
        NodeMatrix[n3 + NODE_OLD_DX] = NodeMatrix[n3 + NODE_DX];
        NodeMatrix[n3 + NODE_OLD_DY] = NodeMatrix[n3 + NODE_DY];
        NodeMatrix[n3 + NODE_DX] = 0;
        NodeMatrix[n3 + NODE_DY] = 0;
      }
      if (options.outboundAttractionDistribution) {
        outboundAttCompensation = 0;
        for (n3 = 0; n3 < order; n3 += PPN) {
          outboundAttCompensation += NodeMatrix[n3 + NODE_MASS];
        }
        outboundAttCompensation /= order / PPN;
      }
      if (options.barnesHutOptimize) {
        var minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity, q, q2, subdivisionAttempts;
        for (n3 = 0; n3 < order; n3 += PPN) {
          minX = Math.min(minX, NodeMatrix[n3 + NODE_X]);
          maxX = Math.max(maxX, NodeMatrix[n3 + NODE_X]);
          minY = Math.min(minY, NodeMatrix[n3 + NODE_Y]);
          maxY = Math.max(maxY, NodeMatrix[n3 + NODE_Y]);
        }
        var dx = maxX - minX, dy = maxY - minY;
        if (dx > dy) {
          minY -= (dx - dy) / 2;
          maxY = minY + dx;
        } else {
          minX -= (dy - dx) / 2;
          maxX = minX + dy;
        }
        RegionMatrix[0 + REGION_NODE] = -1;
        RegionMatrix[0 + REGION_CENTER_X] = (minX + maxX) / 2;
        RegionMatrix[0 + REGION_CENTER_Y] = (minY + maxY) / 2;
        RegionMatrix[0 + REGION_SIZE] = Math.max(maxX - minX, maxY - minY);
        RegionMatrix[0 + REGION_NEXT_SIBLING] = -1;
        RegionMatrix[0 + REGION_FIRST_CHILD] = -1;
        RegionMatrix[0 + REGION_MASS] = 0;
        RegionMatrix[0 + REGION_MASS_CENTER_X] = 0;
        RegionMatrix[0 + REGION_MASS_CENTER_Y] = 0;
        l3 = 1;
        for (n3 = 0; n3 < order; n3 += PPN) {
          r2 = 0;
          subdivisionAttempts = SUBDIVISION_ATTEMPTS;
          while (true) {
            if (RegionMatrix[r2 + REGION_FIRST_CHILD] >= 0) {
              if (NodeMatrix[n3 + NODE_X] < RegionMatrix[r2 + REGION_CENTER_X]) {
                if (NodeMatrix[n3 + NODE_Y] < RegionMatrix[r2 + REGION_CENTER_Y]) {
                  q = RegionMatrix[r2 + REGION_FIRST_CHILD];
                } else {
                  q = RegionMatrix[r2 + REGION_FIRST_CHILD] + PPR;
                }
              } else {
                if (NodeMatrix[n3 + NODE_Y] < RegionMatrix[r2 + REGION_CENTER_Y]) {
                  q = RegionMatrix[r2 + REGION_FIRST_CHILD] + PPR * 2;
                } else {
                  q = RegionMatrix[r2 + REGION_FIRST_CHILD] + PPR * 3;
                }
              }
              RegionMatrix[r2 + REGION_MASS_CENTER_X] = (RegionMatrix[r2 + REGION_MASS_CENTER_X] * RegionMatrix[r2 + REGION_MASS] + NodeMatrix[n3 + NODE_X] * NodeMatrix[n3 + NODE_MASS]) / (RegionMatrix[r2 + REGION_MASS] + NodeMatrix[n3 + NODE_MASS]);
              RegionMatrix[r2 + REGION_MASS_CENTER_Y] = (RegionMatrix[r2 + REGION_MASS_CENTER_Y] * RegionMatrix[r2 + REGION_MASS] + NodeMatrix[n3 + NODE_Y] * NodeMatrix[n3 + NODE_MASS]) / (RegionMatrix[r2 + REGION_MASS] + NodeMatrix[n3 + NODE_MASS]);
              RegionMatrix[r2 + REGION_MASS] += NodeMatrix[n3 + NODE_MASS];
              r2 = q;
              continue;
            } else {
              if (RegionMatrix[r2 + REGION_NODE] < 0) {
                RegionMatrix[r2 + REGION_NODE] = n3;
                break;
              } else {
                RegionMatrix[r2 + REGION_FIRST_CHILD] = l3 * PPR;
                w = RegionMatrix[r2 + REGION_SIZE] / 2;
                g2 = RegionMatrix[r2 + REGION_FIRST_CHILD];
                RegionMatrix[g2 + REGION_NODE] = -1;
                RegionMatrix[g2 + REGION_CENTER_X] = RegionMatrix[r2 + REGION_CENTER_X] - w;
                RegionMatrix[g2 + REGION_CENTER_Y] = RegionMatrix[r2 + REGION_CENTER_Y] - w;
                RegionMatrix[g2 + REGION_SIZE] = w;
                RegionMatrix[g2 + REGION_NEXT_SIBLING] = g2 + PPR;
                RegionMatrix[g2 + REGION_FIRST_CHILD] = -1;
                RegionMatrix[g2 + REGION_MASS] = 0;
                RegionMatrix[g2 + REGION_MASS_CENTER_X] = 0;
                RegionMatrix[g2 + REGION_MASS_CENTER_Y] = 0;
                g2 += PPR;
                RegionMatrix[g2 + REGION_NODE] = -1;
                RegionMatrix[g2 + REGION_CENTER_X] = RegionMatrix[r2 + REGION_CENTER_X] - w;
                RegionMatrix[g2 + REGION_CENTER_Y] = RegionMatrix[r2 + REGION_CENTER_Y] + w;
                RegionMatrix[g2 + REGION_SIZE] = w;
                RegionMatrix[g2 + REGION_NEXT_SIBLING] = g2 + PPR;
                RegionMatrix[g2 + REGION_FIRST_CHILD] = -1;
                RegionMatrix[g2 + REGION_MASS] = 0;
                RegionMatrix[g2 + REGION_MASS_CENTER_X] = 0;
                RegionMatrix[g2 + REGION_MASS_CENTER_Y] = 0;
                g2 += PPR;
                RegionMatrix[g2 + REGION_NODE] = -1;
                RegionMatrix[g2 + REGION_CENTER_X] = RegionMatrix[r2 + REGION_CENTER_X] + w;
                RegionMatrix[g2 + REGION_CENTER_Y] = RegionMatrix[r2 + REGION_CENTER_Y] - w;
                RegionMatrix[g2 + REGION_SIZE] = w;
                RegionMatrix[g2 + REGION_NEXT_SIBLING] = g2 + PPR;
                RegionMatrix[g2 + REGION_FIRST_CHILD] = -1;
                RegionMatrix[g2 + REGION_MASS] = 0;
                RegionMatrix[g2 + REGION_MASS_CENTER_X] = 0;
                RegionMatrix[g2 + REGION_MASS_CENTER_Y] = 0;
                g2 += PPR;
                RegionMatrix[g2 + REGION_NODE] = -1;
                RegionMatrix[g2 + REGION_CENTER_X] = RegionMatrix[r2 + REGION_CENTER_X] + w;
                RegionMatrix[g2 + REGION_CENTER_Y] = RegionMatrix[r2 + REGION_CENTER_Y] + w;
                RegionMatrix[g2 + REGION_SIZE] = w;
                RegionMatrix[g2 + REGION_NEXT_SIBLING] = RegionMatrix[r2 + REGION_NEXT_SIBLING];
                RegionMatrix[g2 + REGION_FIRST_CHILD] = -1;
                RegionMatrix[g2 + REGION_MASS] = 0;
                RegionMatrix[g2 + REGION_MASS_CENTER_X] = 0;
                RegionMatrix[g2 + REGION_MASS_CENTER_Y] = 0;
                l3 += 4;
                if (NodeMatrix[RegionMatrix[r2 + REGION_NODE] + NODE_X] < RegionMatrix[r2 + REGION_CENTER_X]) {
                  if (NodeMatrix[RegionMatrix[r2 + REGION_NODE] + NODE_Y] < RegionMatrix[r2 + REGION_CENTER_Y]) {
                    q = RegionMatrix[r2 + REGION_FIRST_CHILD];
                  } else {
                    q = RegionMatrix[r2 + REGION_FIRST_CHILD] + PPR;
                  }
                } else {
                  if (NodeMatrix[RegionMatrix[r2 + REGION_NODE] + NODE_Y] < RegionMatrix[r2 + REGION_CENTER_Y]) {
                    q = RegionMatrix[r2 + REGION_FIRST_CHILD] + PPR * 2;
                  } else {
                    q = RegionMatrix[r2 + REGION_FIRST_CHILD] + PPR * 3;
                  }
                }
                RegionMatrix[r2 + REGION_MASS] = NodeMatrix[RegionMatrix[r2 + REGION_NODE] + NODE_MASS];
                RegionMatrix[r2 + REGION_MASS_CENTER_X] = NodeMatrix[RegionMatrix[r2 + REGION_NODE] + NODE_X];
                RegionMatrix[r2 + REGION_MASS_CENTER_Y] = NodeMatrix[RegionMatrix[r2 + REGION_NODE] + NODE_Y];
                RegionMatrix[q + REGION_NODE] = RegionMatrix[r2 + REGION_NODE];
                RegionMatrix[r2 + REGION_NODE] = -1;
                if (NodeMatrix[n3 + NODE_X] < RegionMatrix[r2 + REGION_CENTER_X]) {
                  if (NodeMatrix[n3 + NODE_Y] < RegionMatrix[r2 + REGION_CENTER_Y]) {
                    q2 = RegionMatrix[r2 + REGION_FIRST_CHILD];
                  } else {
                    q2 = RegionMatrix[r2 + REGION_FIRST_CHILD] + PPR;
                  }
                } else {
                  if (NodeMatrix[n3 + NODE_Y] < RegionMatrix[r2 + REGION_CENTER_Y]) {
                    q2 = RegionMatrix[r2 + REGION_FIRST_CHILD] + PPR * 2;
                  } else {
                    q2 = RegionMatrix[r2 + REGION_FIRST_CHILD] + PPR * 3;
                  }
                }
                if (q === q2) {
                  if (subdivisionAttempts--) {
                    r2 = q;
                    continue;
                  } else {
                    subdivisionAttempts = SUBDIVISION_ATTEMPTS;
                    break;
                  }
                }
                RegionMatrix[q2 + REGION_NODE] = n3;
                break;
              }
            }
          }
        }
      }
      if (options.barnesHutOptimize) {
        coefficient = options.scalingRatio;
        for (n3 = 0; n3 < order; n3 += PPN) {
          r2 = 0;
          while (true) {
            if (RegionMatrix[r2 + REGION_FIRST_CHILD] >= 0) {
              distance = Math.pow(
                NodeMatrix[n3 + NODE_X] - RegionMatrix[r2 + REGION_MASS_CENTER_X],
                2
              ) + Math.pow(
                NodeMatrix[n3 + NODE_Y] - RegionMatrix[r2 + REGION_MASS_CENTER_Y],
                2
              );
              s3 = RegionMatrix[r2 + REGION_SIZE];
              if (4 * s3 * s3 / distance < thetaSquared) {
                xDist = NodeMatrix[n3 + NODE_X] - RegionMatrix[r2 + REGION_MASS_CENTER_X];
                yDist = NodeMatrix[n3 + NODE_Y] - RegionMatrix[r2 + REGION_MASS_CENTER_Y];
                if (adjustSizes === true) {
                  if (distance > 0) {
                    factor = coefficient * NodeMatrix[n3 + NODE_MASS] * RegionMatrix[r2 + REGION_MASS] / distance;
                    NodeMatrix[n3 + NODE_DX] += xDist * factor;
                    NodeMatrix[n3 + NODE_DY] += yDist * factor;
                  } else if (distance < 0) {
                    factor = -coefficient * NodeMatrix[n3 + NODE_MASS] * RegionMatrix[r2 + REGION_MASS] / Math.sqrt(distance);
                    NodeMatrix[n3 + NODE_DX] += xDist * factor;
                    NodeMatrix[n3 + NODE_DY] += yDist * factor;
                  }
                } else {
                  if (distance > 0) {
                    factor = coefficient * NodeMatrix[n3 + NODE_MASS] * RegionMatrix[r2 + REGION_MASS] / distance;
                    NodeMatrix[n3 + NODE_DX] += xDist * factor;
                    NodeMatrix[n3 + NODE_DY] += yDist * factor;
                  }
                }
                r2 = RegionMatrix[r2 + REGION_NEXT_SIBLING];
                if (r2 < 0) break;
                continue;
              } else {
                r2 = RegionMatrix[r2 + REGION_FIRST_CHILD];
                continue;
              }
            } else {
              rn = RegionMatrix[r2 + REGION_NODE];
              if (rn >= 0 && rn !== n3) {
                xDist = NodeMatrix[n3 + NODE_X] - NodeMatrix[rn + NODE_X];
                yDist = NodeMatrix[n3 + NODE_Y] - NodeMatrix[rn + NODE_Y];
                distance = xDist * xDist + yDist * yDist;
                if (adjustSizes === true) {
                  if (distance > 0) {
                    factor = coefficient * NodeMatrix[n3 + NODE_MASS] * NodeMatrix[rn + NODE_MASS] / distance;
                    NodeMatrix[n3 + NODE_DX] += xDist * factor;
                    NodeMatrix[n3 + NODE_DY] += yDist * factor;
                  } else if (distance < 0) {
                    factor = -coefficient * NodeMatrix[n3 + NODE_MASS] * NodeMatrix[rn + NODE_MASS] / Math.sqrt(distance);
                    NodeMatrix[n3 + NODE_DX] += xDist * factor;
                    NodeMatrix[n3 + NODE_DY] += yDist * factor;
                  }
                } else {
                  if (distance > 0) {
                    factor = coefficient * NodeMatrix[n3 + NODE_MASS] * NodeMatrix[rn + NODE_MASS] / distance;
                    NodeMatrix[n3 + NODE_DX] += xDist * factor;
                    NodeMatrix[n3 + NODE_DY] += yDist * factor;
                  }
                }
              }
              r2 = RegionMatrix[r2 + REGION_NEXT_SIBLING];
              if (r2 < 0) break;
              continue;
            }
          }
        }
      } else {
        coefficient = options.scalingRatio;
        for (n1 = 0; n1 < order; n1 += PPN) {
          for (n22 = 0; n22 < n1; n22 += PPN) {
            xDist = NodeMatrix[n1 + NODE_X] - NodeMatrix[n22 + NODE_X];
            yDist = NodeMatrix[n1 + NODE_Y] - NodeMatrix[n22 + NODE_Y];
            if (adjustSizes === true) {
              distance = Math.sqrt(xDist * xDist + yDist * yDist) - NodeMatrix[n1 + NODE_SIZE] - NodeMatrix[n22 + NODE_SIZE];
              if (distance > 0) {
                factor = coefficient * NodeMatrix[n1 + NODE_MASS] * NodeMatrix[n22 + NODE_MASS] / distance / distance;
                NodeMatrix[n1 + NODE_DX] += xDist * factor;
                NodeMatrix[n1 + NODE_DY] += yDist * factor;
                NodeMatrix[n22 + NODE_DX] -= xDist * factor;
                NodeMatrix[n22 + NODE_DY] -= yDist * factor;
              } else if (distance < 0) {
                factor = 100 * coefficient * NodeMatrix[n1 + NODE_MASS] * NodeMatrix[n22 + NODE_MASS];
                NodeMatrix[n1 + NODE_DX] += xDist * factor;
                NodeMatrix[n1 + NODE_DY] += yDist * factor;
                NodeMatrix[n22 + NODE_DX] -= xDist * factor;
                NodeMatrix[n22 + NODE_DY] -= yDist * factor;
              }
            } else {
              distance = Math.sqrt(xDist * xDist + yDist * yDist);
              if (distance > 0) {
                factor = coefficient * NodeMatrix[n1 + NODE_MASS] * NodeMatrix[n22 + NODE_MASS] / distance / distance;
                NodeMatrix[n1 + NODE_DX] += xDist * factor;
                NodeMatrix[n1 + NODE_DY] += yDist * factor;
                NodeMatrix[n22 + NODE_DX] -= xDist * factor;
                NodeMatrix[n22 + NODE_DY] -= yDist * factor;
              }
            }
          }
        }
      }
      g2 = options.gravity / options.scalingRatio;
      coefficient = options.scalingRatio;
      for (n3 = 0; n3 < order; n3 += PPN) {
        factor = 0;
        xDist = NodeMatrix[n3 + NODE_X];
        yDist = NodeMatrix[n3 + NODE_Y];
        distance = Math.sqrt(Math.pow(xDist, 2) + Math.pow(yDist, 2));
        if (options.strongGravityMode) {
          if (distance > 0) factor = coefficient * NodeMatrix[n3 + NODE_MASS] * g2;
        } else {
          if (distance > 0)
            factor = coefficient * NodeMatrix[n3 + NODE_MASS] * g2 / distance;
        }
        NodeMatrix[n3 + NODE_DX] -= xDist * factor;
        NodeMatrix[n3 + NODE_DY] -= yDist * factor;
      }
      coefficient = 1 * (options.outboundAttractionDistribution ? outboundAttCompensation : 1);
      for (e2 = 0; e2 < size; e2 += PPE) {
        n1 = EdgeMatrix[e2 + EDGE_SOURCE];
        n22 = EdgeMatrix[e2 + EDGE_TARGET];
        w = EdgeMatrix[e2 + EDGE_WEIGHT];
        ewc = Math.pow(w, options.edgeWeightInfluence);
        xDist = NodeMatrix[n1 + NODE_X] - NodeMatrix[n22 + NODE_X];
        yDist = NodeMatrix[n1 + NODE_Y] - NodeMatrix[n22 + NODE_Y];
        if (adjustSizes === true) {
          distance = Math.sqrt(xDist * xDist + yDist * yDist) - NodeMatrix[n1 + NODE_SIZE] - NodeMatrix[n22 + NODE_SIZE];
          if (options.linLogMode) {
            if (options.outboundAttractionDistribution) {
              if (distance > 0) {
                factor = -coefficient * ewc * Math.log(1 + distance) / distance / NodeMatrix[n1 + NODE_MASS];
              }
            } else {
              if (distance > 0) {
                factor = -coefficient * ewc * Math.log(1 + distance) / distance;
              }
            }
          } else {
            if (options.outboundAttractionDistribution) {
              if (distance > 0) {
                factor = -coefficient * ewc / NodeMatrix[n1 + NODE_MASS];
              }
            } else {
              if (distance > 0) {
                factor = -coefficient * ewc;
              }
            }
          }
        } else {
          distance = Math.sqrt(Math.pow(xDist, 2) + Math.pow(yDist, 2));
          if (options.linLogMode) {
            if (options.outboundAttractionDistribution) {
              if (distance > 0) {
                factor = -coefficient * ewc * Math.log(1 + distance) / distance / NodeMatrix[n1 + NODE_MASS];
              }
            } else {
              if (distance > 0)
                factor = -coefficient * ewc * Math.log(1 + distance) / distance;
            }
          } else {
            if (options.outboundAttractionDistribution) {
              distance = 1;
              factor = -coefficient * ewc / NodeMatrix[n1 + NODE_MASS];
            } else {
              distance = 1;
              factor = -coefficient * ewc;
            }
          }
        }
        if (distance > 0) {
          NodeMatrix[n1 + NODE_DX] += xDist * factor;
          NodeMatrix[n1 + NODE_DY] += yDist * factor;
          NodeMatrix[n22 + NODE_DX] -= xDist * factor;
          NodeMatrix[n22 + NODE_DY] -= yDist * factor;
        }
      }
      var force, swinging, traction, nodespeed, newX, newY;
      if (adjustSizes === true) {
        for (n3 = 0; n3 < order; n3 += PPN) {
          if (NodeMatrix[n3 + NODE_FIXED] !== 1) {
            force = Math.sqrt(
              Math.pow(NodeMatrix[n3 + NODE_DX], 2) + Math.pow(NodeMatrix[n3 + NODE_DY], 2)
            );
            if (force > MAX_FORCE) {
              NodeMatrix[n3 + NODE_DX] = NodeMatrix[n3 + NODE_DX] * MAX_FORCE / force;
              NodeMatrix[n3 + NODE_DY] = NodeMatrix[n3 + NODE_DY] * MAX_FORCE / force;
            }
            swinging = NodeMatrix[n3 + NODE_MASS] * Math.sqrt(
              (NodeMatrix[n3 + NODE_OLD_DX] - NodeMatrix[n3 + NODE_DX]) * (NodeMatrix[n3 + NODE_OLD_DX] - NodeMatrix[n3 + NODE_DX]) + (NodeMatrix[n3 + NODE_OLD_DY] - NodeMatrix[n3 + NODE_DY]) * (NodeMatrix[n3 + NODE_OLD_DY] - NodeMatrix[n3 + NODE_DY])
            );
            traction = Math.sqrt(
              (NodeMatrix[n3 + NODE_OLD_DX] + NodeMatrix[n3 + NODE_DX]) * (NodeMatrix[n3 + NODE_OLD_DX] + NodeMatrix[n3 + NODE_DX]) + (NodeMatrix[n3 + NODE_OLD_DY] + NodeMatrix[n3 + NODE_DY]) * (NodeMatrix[n3 + NODE_OLD_DY] + NodeMatrix[n3 + NODE_DY])
            ) / 2;
            nodespeed = 0.1 * Math.log(1 + traction) / (1 + Math.sqrt(swinging));
            newX = NodeMatrix[n3 + NODE_X] + NodeMatrix[n3 + NODE_DX] * (nodespeed / options.slowDown);
            NodeMatrix[n3 + NODE_X] = newX;
            newY = NodeMatrix[n3 + NODE_Y] + NodeMatrix[n3 + NODE_DY] * (nodespeed / options.slowDown);
            NodeMatrix[n3 + NODE_Y] = newY;
          }
        }
      } else {
        for (n3 = 0; n3 < order; n3 += PPN) {
          if (NodeMatrix[n3 + NODE_FIXED] !== 1) {
            swinging = NodeMatrix[n3 + NODE_MASS] * Math.sqrt(
              (NodeMatrix[n3 + NODE_OLD_DX] - NodeMatrix[n3 + NODE_DX]) * (NodeMatrix[n3 + NODE_OLD_DX] - NodeMatrix[n3 + NODE_DX]) + (NodeMatrix[n3 + NODE_OLD_DY] - NodeMatrix[n3 + NODE_DY]) * (NodeMatrix[n3 + NODE_OLD_DY] - NodeMatrix[n3 + NODE_DY])
            );
            traction = Math.sqrt(
              (NodeMatrix[n3 + NODE_OLD_DX] + NodeMatrix[n3 + NODE_DX]) * (NodeMatrix[n3 + NODE_OLD_DX] + NodeMatrix[n3 + NODE_DX]) + (NodeMatrix[n3 + NODE_OLD_DY] + NodeMatrix[n3 + NODE_DY]) * (NodeMatrix[n3 + NODE_OLD_DY] + NodeMatrix[n3 + NODE_DY])
            ) / 2;
            nodespeed = NodeMatrix[n3 + NODE_CONVERGENCE] * Math.log(1 + traction) / (1 + Math.sqrt(swinging));
            NodeMatrix[n3 + NODE_CONVERGENCE] = Math.min(
              1,
              Math.sqrt(
                nodespeed * (Math.pow(NodeMatrix[n3 + NODE_DX], 2) + Math.pow(NodeMatrix[n3 + NODE_DY], 2)) / (1 + Math.sqrt(swinging))
              )
            );
            newX = NodeMatrix[n3 + NODE_X] + NodeMatrix[n3 + NODE_DX] * (nodespeed / options.slowDown);
            NodeMatrix[n3 + NODE_X] = newX;
            newY = NodeMatrix[n3 + NODE_Y] + NodeMatrix[n3 + NODE_DY] * (nodespeed / options.slowDown);
            NodeMatrix[n3 + NODE_Y] = newY;
          }
        }
      }
      return {};
    };
  }
});

// node_modules/graphology-layout-forceatlas2/helpers.js
var require_helpers = __commonJS({
  "node_modules/graphology-layout-forceatlas2/helpers.js"(exports) {
    var PPN = 10;
    var PPE = 3;
    exports.assign = function(target) {
      target = target || {};
      var objects = Array.prototype.slice.call(arguments).slice(1), i2, k, l3;
      for (i2 = 0, l3 = objects.length; i2 < l3; i2++) {
        if (!objects[i2]) continue;
        for (k in objects[i2]) target[k] = objects[i2][k];
      }
      return target;
    };
    exports.validateSettings = function(settings) {
      if ("linLogMode" in settings && typeof settings.linLogMode !== "boolean")
        return { message: "the `linLogMode` setting should be a boolean." };
      if ("outboundAttractionDistribution" in settings && typeof settings.outboundAttractionDistribution !== "boolean")
        return {
          message: "the `outboundAttractionDistribution` setting should be a boolean."
        };
      if ("adjustSizes" in settings && typeof settings.adjustSizes !== "boolean")
        return { message: "the `adjustSizes` setting should be a boolean." };
      if ("edgeWeightInfluence" in settings && typeof settings.edgeWeightInfluence !== "number")
        return {
          message: "the `edgeWeightInfluence` setting should be a number."
        };
      if ("scalingRatio" in settings && !(typeof settings.scalingRatio === "number" && settings.scalingRatio >= 0))
        return { message: "the `scalingRatio` setting should be a number >= 0." };
      if ("strongGravityMode" in settings && typeof settings.strongGravityMode !== "boolean")
        return { message: "the `strongGravityMode` setting should be a boolean." };
      if ("gravity" in settings && !(typeof settings.gravity === "number" && settings.gravity >= 0))
        return { message: "the `gravity` setting should be a number >= 0." };
      if ("slowDown" in settings && !(typeof settings.slowDown === "number" || settings.slowDown >= 0))
        return { message: "the `slowDown` setting should be a number >= 0." };
      if ("barnesHutOptimize" in settings && typeof settings.barnesHutOptimize !== "boolean")
        return { message: "the `barnesHutOptimize` setting should be a boolean." };
      if ("barnesHutTheta" in settings && !(typeof settings.barnesHutTheta === "number" && settings.barnesHutTheta >= 0))
        return { message: "the `barnesHutTheta` setting should be a number >= 0." };
      return null;
    };
    exports.graphToByteArrays = function(graph, getEdgeWeight) {
      var order = graph.order;
      var size = graph.size;
      var index = {};
      var j2;
      var NodeMatrix = new Float32Array(order * PPN);
      var EdgeMatrix = new Float32Array(size * PPE);
      j2 = 0;
      graph.forEachNode(function(node, attr) {
        index[node] = j2;
        NodeMatrix[j2] = attr.x;
        NodeMatrix[j2 + 1] = attr.y;
        NodeMatrix[j2 + 2] = 0;
        NodeMatrix[j2 + 3] = 0;
        NodeMatrix[j2 + 4] = 0;
        NodeMatrix[j2 + 5] = 0;
        NodeMatrix[j2 + 6] = 1;
        NodeMatrix[j2 + 7] = 1;
        NodeMatrix[j2 + 8] = attr.size || 1;
        NodeMatrix[j2 + 9] = attr.fixed ? 1 : 0;
        j2 += PPN;
      });
      j2 = 0;
      graph.forEachEdge(function(edge, attr, source, target, sa, ta, u2) {
        var sj = index[source];
        var tj = index[target];
        var weight = getEdgeWeight(edge, attr, source, target, sa, ta, u2);
        NodeMatrix[sj + 6] += weight;
        NodeMatrix[tj + 6] += weight;
        EdgeMatrix[j2] = sj;
        EdgeMatrix[j2 + 1] = tj;
        EdgeMatrix[j2 + 2] = weight;
        j2 += PPE;
      });
      return {
        nodes: NodeMatrix,
        edges: EdgeMatrix
      };
    };
    exports.assignLayoutChanges = function(graph, NodeMatrix, outputReducer) {
      var i2 = 0;
      graph.updateEachNodeAttributes(function(node, attr) {
        attr.x = NodeMatrix[i2];
        attr.y = NodeMatrix[i2 + 1];
        i2 += PPN;
        return outputReducer ? outputReducer(node, attr) : attr;
      });
    };
    exports.readGraphPositions = function(graph, NodeMatrix) {
      var i2 = 0;
      graph.forEachNode(function(node, attr) {
        NodeMatrix[i2] = attr.x;
        NodeMatrix[i2 + 1] = attr.y;
        i2 += PPN;
      });
    };
    exports.collectLayoutChanges = function(graph, NodeMatrix, outputReducer) {
      var nodes = graph.nodes(), positions = {};
      for (var i2 = 0, j2 = 0, l3 = NodeMatrix.length; i2 < l3; i2 += PPN) {
        if (outputReducer) {
          var newAttr = Object.assign({}, graph.getNodeAttributes(nodes[j2]));
          newAttr.x = NodeMatrix[i2];
          newAttr.y = NodeMatrix[i2 + 1];
          newAttr = outputReducer(nodes[j2], newAttr);
          positions[nodes[j2]] = {
            x: newAttr.x,
            y: newAttr.y
          };
        } else {
          positions[nodes[j2]] = {
            x: NodeMatrix[i2],
            y: NodeMatrix[i2 + 1]
          };
        }
        j2++;
      }
      return positions;
    };
    exports.createWorker = function createWorker(fn) {
      var xURL = window.URL || window.webkitURL;
      var code = fn.toString();
      var objectUrl = xURL.createObjectURL(
        new Blob(["(" + code + ").call(this);"], { type: "text/javascript" })
      );
      var worker = new Worker(objectUrl);
      xURL.revokeObjectURL(objectUrl);
      return worker;
    };
  }
});

// node_modules/graphology-layout-forceatlas2/defaults.js
var require_defaults = __commonJS({
  "node_modules/graphology-layout-forceatlas2/defaults.js"(exports, module) {
    module.exports = {
      linLogMode: false,
      outboundAttractionDistribution: false,
      adjustSizes: false,
      edgeWeightInfluence: 1,
      scalingRatio: 1,
      strongGravityMode: false,
      gravity: 1,
      slowDown: 1,
      barnesHutOptimize: false,
      barnesHutTheta: 0.5
    };
  }
});

// node_modules/graphology-layout-forceatlas2/index.js
var require_graphology_layout_forceatlas2 = __commonJS({
  "node_modules/graphology-layout-forceatlas2/index.js"(exports, module) {
    var isGraph = require_is_graph();
    var createEdgeWeightGetter = require_getters().createEdgeWeightGetter;
    var iterate = require_iterate();
    var helpers = require_helpers();
    var DEFAULT_SETTINGS = require_defaults();
    function abstractSynchronousLayout(assign, graph, params) {
      if (!isGraph(graph))
        throw new Error(
          "graphology-layout-forceatlas2: the given graph is not a valid graphology instance."
        );
      if (typeof params === "number") params = { iterations: params };
      var iterations = params.iterations;
      if (typeof iterations !== "number")
        throw new Error(
          "graphology-layout-forceatlas2: invalid number of iterations."
        );
      if (iterations <= 0)
        throw new Error(
          "graphology-layout-forceatlas2: you should provide a positive number of iterations."
        );
      var getEdgeWeight = createEdgeWeightGetter(
        "getEdgeWeight" in params ? params.getEdgeWeight : "weight"
      ).fromEntry;
      var outputReducer = typeof params.outputReducer === "function" ? params.outputReducer : null;
      var settings = helpers.assign({}, DEFAULT_SETTINGS, params.settings);
      var validationError = helpers.validateSettings(settings);
      if (validationError)
        throw new Error(
          "graphology-layout-forceatlas2: " + validationError.message
        );
      var matrices = helpers.graphToByteArrays(graph, getEdgeWeight);
      var i2;
      for (i2 = 0; i2 < iterations; i2++)
        iterate(settings, matrices.nodes, matrices.edges);
      if (assign) {
        helpers.assignLayoutChanges(graph, matrices.nodes, outputReducer);
        return;
      }
      return helpers.collectLayoutChanges(graph, matrices.nodes);
    }
    function inferSettings(graph) {
      var order = typeof graph === "number" ? graph : graph.order;
      return {
        barnesHutOptimize: order > 2e3,
        strongGravityMode: true,
        gravity: 0.05,
        scalingRatio: 10,
        slowDown: 1 + Math.log(order)
      };
    }
    var synchronousLayout = abstractSynchronousLayout.bind(null, false);
    synchronousLayout.assign = abstractSynchronousLayout.bind(null, true);
    synchronousLayout.inferSettings = inferSettings;
    module.exports = synchronousLayout;
  }
});

// node_modules/graphology-layout-forceatlas2/webworker.js
var require_webworker = __commonJS({
  "node_modules/graphology-layout-forceatlas2/webworker.js"(exports, module) {
    module.exports = function worker() {
      var NODES, EDGES;
      var moduleShim = {};
      (function() {
        var NODE_X = 0;
        var NODE_Y = 1;
        var NODE_DX = 2;
        var NODE_DY = 3;
        var NODE_OLD_DX = 4;
        var NODE_OLD_DY = 5;
        var NODE_MASS = 6;
        var NODE_CONVERGENCE = 7;
        var NODE_SIZE = 8;
        var NODE_FIXED = 9;
        var EDGE_SOURCE = 0;
        var EDGE_TARGET = 1;
        var EDGE_WEIGHT = 2;
        var REGION_NODE = 0;
        var REGION_CENTER_X = 1;
        var REGION_CENTER_Y = 2;
        var REGION_SIZE = 3;
        var REGION_NEXT_SIBLING = 4;
        var REGION_FIRST_CHILD = 5;
        var REGION_MASS = 6;
        var REGION_MASS_CENTER_X = 7;
        var REGION_MASS_CENTER_Y = 8;
        var SUBDIVISION_ATTEMPTS = 3;
        var PPN = 10;
        var PPE = 3;
        var PPR = 9;
        var MAX_FORCE = 10;
        moduleShim.exports = function iterate2(options, NodeMatrix, EdgeMatrix) {
          var l3, r2, n3, n1, n22, rn, e2, w, g2, s3;
          var order = NodeMatrix.length, size = EdgeMatrix.length;
          var adjustSizes = options.adjustSizes;
          var thetaSquared = options.barnesHutTheta * options.barnesHutTheta;
          var outboundAttCompensation, coefficient, xDist, yDist, ewc, distance, factor;
          var RegionMatrix = [];
          for (n3 = 0; n3 < order; n3 += PPN) {
            NodeMatrix[n3 + NODE_OLD_DX] = NodeMatrix[n3 + NODE_DX];
            NodeMatrix[n3 + NODE_OLD_DY] = NodeMatrix[n3 + NODE_DY];
            NodeMatrix[n3 + NODE_DX] = 0;
            NodeMatrix[n3 + NODE_DY] = 0;
          }
          if (options.outboundAttractionDistribution) {
            outboundAttCompensation = 0;
            for (n3 = 0; n3 < order; n3 += PPN) {
              outboundAttCompensation += NodeMatrix[n3 + NODE_MASS];
            }
            outboundAttCompensation /= order / PPN;
          }
          if (options.barnesHutOptimize) {
            var minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity, q, q2, subdivisionAttempts;
            for (n3 = 0; n3 < order; n3 += PPN) {
              minX = Math.min(minX, NodeMatrix[n3 + NODE_X]);
              maxX = Math.max(maxX, NodeMatrix[n3 + NODE_X]);
              minY = Math.min(minY, NodeMatrix[n3 + NODE_Y]);
              maxY = Math.max(maxY, NodeMatrix[n3 + NODE_Y]);
            }
            var dx = maxX - minX, dy = maxY - minY;
            if (dx > dy) {
              minY -= (dx - dy) / 2;
              maxY = minY + dx;
            } else {
              minX -= (dy - dx) / 2;
              maxX = minX + dy;
            }
            RegionMatrix[0 + REGION_NODE] = -1;
            RegionMatrix[0 + REGION_CENTER_X] = (minX + maxX) / 2;
            RegionMatrix[0 + REGION_CENTER_Y] = (minY + maxY) / 2;
            RegionMatrix[0 + REGION_SIZE] = Math.max(maxX - minX, maxY - minY);
            RegionMatrix[0 + REGION_NEXT_SIBLING] = -1;
            RegionMatrix[0 + REGION_FIRST_CHILD] = -1;
            RegionMatrix[0 + REGION_MASS] = 0;
            RegionMatrix[0 + REGION_MASS_CENTER_X] = 0;
            RegionMatrix[0 + REGION_MASS_CENTER_Y] = 0;
            l3 = 1;
            for (n3 = 0; n3 < order; n3 += PPN) {
              r2 = 0;
              subdivisionAttempts = SUBDIVISION_ATTEMPTS;
              while (true) {
                if (RegionMatrix[r2 + REGION_FIRST_CHILD] >= 0) {
                  if (NodeMatrix[n3 + NODE_X] < RegionMatrix[r2 + REGION_CENTER_X]) {
                    if (NodeMatrix[n3 + NODE_Y] < RegionMatrix[r2 + REGION_CENTER_Y]) {
                      q = RegionMatrix[r2 + REGION_FIRST_CHILD];
                    } else {
                      q = RegionMatrix[r2 + REGION_FIRST_CHILD] + PPR;
                    }
                  } else {
                    if (NodeMatrix[n3 + NODE_Y] < RegionMatrix[r2 + REGION_CENTER_Y]) {
                      q = RegionMatrix[r2 + REGION_FIRST_CHILD] + PPR * 2;
                    } else {
                      q = RegionMatrix[r2 + REGION_FIRST_CHILD] + PPR * 3;
                    }
                  }
                  RegionMatrix[r2 + REGION_MASS_CENTER_X] = (RegionMatrix[r2 + REGION_MASS_CENTER_X] * RegionMatrix[r2 + REGION_MASS] + NodeMatrix[n3 + NODE_X] * NodeMatrix[n3 + NODE_MASS]) / (RegionMatrix[r2 + REGION_MASS] + NodeMatrix[n3 + NODE_MASS]);
                  RegionMatrix[r2 + REGION_MASS_CENTER_Y] = (RegionMatrix[r2 + REGION_MASS_CENTER_Y] * RegionMatrix[r2 + REGION_MASS] + NodeMatrix[n3 + NODE_Y] * NodeMatrix[n3 + NODE_MASS]) / (RegionMatrix[r2 + REGION_MASS] + NodeMatrix[n3 + NODE_MASS]);
                  RegionMatrix[r2 + REGION_MASS] += NodeMatrix[n3 + NODE_MASS];
                  r2 = q;
                  continue;
                } else {
                  if (RegionMatrix[r2 + REGION_NODE] < 0) {
                    RegionMatrix[r2 + REGION_NODE] = n3;
                    break;
                  } else {
                    RegionMatrix[r2 + REGION_FIRST_CHILD] = l3 * PPR;
                    w = RegionMatrix[r2 + REGION_SIZE] / 2;
                    g2 = RegionMatrix[r2 + REGION_FIRST_CHILD];
                    RegionMatrix[g2 + REGION_NODE] = -1;
                    RegionMatrix[g2 + REGION_CENTER_X] = RegionMatrix[r2 + REGION_CENTER_X] - w;
                    RegionMatrix[g2 + REGION_CENTER_Y] = RegionMatrix[r2 + REGION_CENTER_Y] - w;
                    RegionMatrix[g2 + REGION_SIZE] = w;
                    RegionMatrix[g2 + REGION_NEXT_SIBLING] = g2 + PPR;
                    RegionMatrix[g2 + REGION_FIRST_CHILD] = -1;
                    RegionMatrix[g2 + REGION_MASS] = 0;
                    RegionMatrix[g2 + REGION_MASS_CENTER_X] = 0;
                    RegionMatrix[g2 + REGION_MASS_CENTER_Y] = 0;
                    g2 += PPR;
                    RegionMatrix[g2 + REGION_NODE] = -1;
                    RegionMatrix[g2 + REGION_CENTER_X] = RegionMatrix[r2 + REGION_CENTER_X] - w;
                    RegionMatrix[g2 + REGION_CENTER_Y] = RegionMatrix[r2 + REGION_CENTER_Y] + w;
                    RegionMatrix[g2 + REGION_SIZE] = w;
                    RegionMatrix[g2 + REGION_NEXT_SIBLING] = g2 + PPR;
                    RegionMatrix[g2 + REGION_FIRST_CHILD] = -1;
                    RegionMatrix[g2 + REGION_MASS] = 0;
                    RegionMatrix[g2 + REGION_MASS_CENTER_X] = 0;
                    RegionMatrix[g2 + REGION_MASS_CENTER_Y] = 0;
                    g2 += PPR;
                    RegionMatrix[g2 + REGION_NODE] = -1;
                    RegionMatrix[g2 + REGION_CENTER_X] = RegionMatrix[r2 + REGION_CENTER_X] + w;
                    RegionMatrix[g2 + REGION_CENTER_Y] = RegionMatrix[r2 + REGION_CENTER_Y] - w;
                    RegionMatrix[g2 + REGION_SIZE] = w;
                    RegionMatrix[g2 + REGION_NEXT_SIBLING] = g2 + PPR;
                    RegionMatrix[g2 + REGION_FIRST_CHILD] = -1;
                    RegionMatrix[g2 + REGION_MASS] = 0;
                    RegionMatrix[g2 + REGION_MASS_CENTER_X] = 0;
                    RegionMatrix[g2 + REGION_MASS_CENTER_Y] = 0;
                    g2 += PPR;
                    RegionMatrix[g2 + REGION_NODE] = -1;
                    RegionMatrix[g2 + REGION_CENTER_X] = RegionMatrix[r2 + REGION_CENTER_X] + w;
                    RegionMatrix[g2 + REGION_CENTER_Y] = RegionMatrix[r2 + REGION_CENTER_Y] + w;
                    RegionMatrix[g2 + REGION_SIZE] = w;
                    RegionMatrix[g2 + REGION_NEXT_SIBLING] = RegionMatrix[r2 + REGION_NEXT_SIBLING];
                    RegionMatrix[g2 + REGION_FIRST_CHILD] = -1;
                    RegionMatrix[g2 + REGION_MASS] = 0;
                    RegionMatrix[g2 + REGION_MASS_CENTER_X] = 0;
                    RegionMatrix[g2 + REGION_MASS_CENTER_Y] = 0;
                    l3 += 4;
                    if (NodeMatrix[RegionMatrix[r2 + REGION_NODE] + NODE_X] < RegionMatrix[r2 + REGION_CENTER_X]) {
                      if (NodeMatrix[RegionMatrix[r2 + REGION_NODE] + NODE_Y] < RegionMatrix[r2 + REGION_CENTER_Y]) {
                        q = RegionMatrix[r2 + REGION_FIRST_CHILD];
                      } else {
                        q = RegionMatrix[r2 + REGION_FIRST_CHILD] + PPR;
                      }
                    } else {
                      if (NodeMatrix[RegionMatrix[r2 + REGION_NODE] + NODE_Y] < RegionMatrix[r2 + REGION_CENTER_Y]) {
                        q = RegionMatrix[r2 + REGION_FIRST_CHILD] + PPR * 2;
                      } else {
                        q = RegionMatrix[r2 + REGION_FIRST_CHILD] + PPR * 3;
                      }
                    }
                    RegionMatrix[r2 + REGION_MASS] = NodeMatrix[RegionMatrix[r2 + REGION_NODE] + NODE_MASS];
                    RegionMatrix[r2 + REGION_MASS_CENTER_X] = NodeMatrix[RegionMatrix[r2 + REGION_NODE] + NODE_X];
                    RegionMatrix[r2 + REGION_MASS_CENTER_Y] = NodeMatrix[RegionMatrix[r2 + REGION_NODE] + NODE_Y];
                    RegionMatrix[q + REGION_NODE] = RegionMatrix[r2 + REGION_NODE];
                    RegionMatrix[r2 + REGION_NODE] = -1;
                    if (NodeMatrix[n3 + NODE_X] < RegionMatrix[r2 + REGION_CENTER_X]) {
                      if (NodeMatrix[n3 + NODE_Y] < RegionMatrix[r2 + REGION_CENTER_Y]) {
                        q2 = RegionMatrix[r2 + REGION_FIRST_CHILD];
                      } else {
                        q2 = RegionMatrix[r2 + REGION_FIRST_CHILD] + PPR;
                      }
                    } else {
                      if (NodeMatrix[n3 + NODE_Y] < RegionMatrix[r2 + REGION_CENTER_Y]) {
                        q2 = RegionMatrix[r2 + REGION_FIRST_CHILD] + PPR * 2;
                      } else {
                        q2 = RegionMatrix[r2 + REGION_FIRST_CHILD] + PPR * 3;
                      }
                    }
                    if (q === q2) {
                      if (subdivisionAttempts--) {
                        r2 = q;
                        continue;
                      } else {
                        subdivisionAttempts = SUBDIVISION_ATTEMPTS;
                        break;
                      }
                    }
                    RegionMatrix[q2 + REGION_NODE] = n3;
                    break;
                  }
                }
              }
            }
          }
          if (options.barnesHutOptimize) {
            coefficient = options.scalingRatio;
            for (n3 = 0; n3 < order; n3 += PPN) {
              r2 = 0;
              while (true) {
                if (RegionMatrix[r2 + REGION_FIRST_CHILD] >= 0) {
                  distance = Math.pow(
                    NodeMatrix[n3 + NODE_X] - RegionMatrix[r2 + REGION_MASS_CENTER_X],
                    2
                  ) + Math.pow(
                    NodeMatrix[n3 + NODE_Y] - RegionMatrix[r2 + REGION_MASS_CENTER_Y],
                    2
                  );
                  s3 = RegionMatrix[r2 + REGION_SIZE];
                  if (4 * s3 * s3 / distance < thetaSquared) {
                    xDist = NodeMatrix[n3 + NODE_X] - RegionMatrix[r2 + REGION_MASS_CENTER_X];
                    yDist = NodeMatrix[n3 + NODE_Y] - RegionMatrix[r2 + REGION_MASS_CENTER_Y];
                    if (adjustSizes === true) {
                      if (distance > 0) {
                        factor = coefficient * NodeMatrix[n3 + NODE_MASS] * RegionMatrix[r2 + REGION_MASS] / distance;
                        NodeMatrix[n3 + NODE_DX] += xDist * factor;
                        NodeMatrix[n3 + NODE_DY] += yDist * factor;
                      } else if (distance < 0) {
                        factor = -coefficient * NodeMatrix[n3 + NODE_MASS] * RegionMatrix[r2 + REGION_MASS] / Math.sqrt(distance);
                        NodeMatrix[n3 + NODE_DX] += xDist * factor;
                        NodeMatrix[n3 + NODE_DY] += yDist * factor;
                      }
                    } else {
                      if (distance > 0) {
                        factor = coefficient * NodeMatrix[n3 + NODE_MASS] * RegionMatrix[r2 + REGION_MASS] / distance;
                        NodeMatrix[n3 + NODE_DX] += xDist * factor;
                        NodeMatrix[n3 + NODE_DY] += yDist * factor;
                      }
                    }
                    r2 = RegionMatrix[r2 + REGION_NEXT_SIBLING];
                    if (r2 < 0) break;
                    continue;
                  } else {
                    r2 = RegionMatrix[r2 + REGION_FIRST_CHILD];
                    continue;
                  }
                } else {
                  rn = RegionMatrix[r2 + REGION_NODE];
                  if (rn >= 0 && rn !== n3) {
                    xDist = NodeMatrix[n3 + NODE_X] - NodeMatrix[rn + NODE_X];
                    yDist = NodeMatrix[n3 + NODE_Y] - NodeMatrix[rn + NODE_Y];
                    distance = xDist * xDist + yDist * yDist;
                    if (adjustSizes === true) {
                      if (distance > 0) {
                        factor = coefficient * NodeMatrix[n3 + NODE_MASS] * NodeMatrix[rn + NODE_MASS] / distance;
                        NodeMatrix[n3 + NODE_DX] += xDist * factor;
                        NodeMatrix[n3 + NODE_DY] += yDist * factor;
                      } else if (distance < 0) {
                        factor = -coefficient * NodeMatrix[n3 + NODE_MASS] * NodeMatrix[rn + NODE_MASS] / Math.sqrt(distance);
                        NodeMatrix[n3 + NODE_DX] += xDist * factor;
                        NodeMatrix[n3 + NODE_DY] += yDist * factor;
                      }
                    } else {
                      if (distance > 0) {
                        factor = coefficient * NodeMatrix[n3 + NODE_MASS] * NodeMatrix[rn + NODE_MASS] / distance;
                        NodeMatrix[n3 + NODE_DX] += xDist * factor;
                        NodeMatrix[n3 + NODE_DY] += yDist * factor;
                      }
                    }
                  }
                  r2 = RegionMatrix[r2 + REGION_NEXT_SIBLING];
                  if (r2 < 0) break;
                  continue;
                }
              }
            }
          } else {
            coefficient = options.scalingRatio;
            for (n1 = 0; n1 < order; n1 += PPN) {
              for (n22 = 0; n22 < n1; n22 += PPN) {
                xDist = NodeMatrix[n1 + NODE_X] - NodeMatrix[n22 + NODE_X];
                yDist = NodeMatrix[n1 + NODE_Y] - NodeMatrix[n22 + NODE_Y];
                if (adjustSizes === true) {
                  distance = Math.sqrt(xDist * xDist + yDist * yDist) - NodeMatrix[n1 + NODE_SIZE] - NodeMatrix[n22 + NODE_SIZE];
                  if (distance > 0) {
                    factor = coefficient * NodeMatrix[n1 + NODE_MASS] * NodeMatrix[n22 + NODE_MASS] / distance / distance;
                    NodeMatrix[n1 + NODE_DX] += xDist * factor;
                    NodeMatrix[n1 + NODE_DY] += yDist * factor;
                    NodeMatrix[n22 + NODE_DX] -= xDist * factor;
                    NodeMatrix[n22 + NODE_DY] -= yDist * factor;
                  } else if (distance < 0) {
                    factor = 100 * coefficient * NodeMatrix[n1 + NODE_MASS] * NodeMatrix[n22 + NODE_MASS];
                    NodeMatrix[n1 + NODE_DX] += xDist * factor;
                    NodeMatrix[n1 + NODE_DY] += yDist * factor;
                    NodeMatrix[n22 + NODE_DX] -= xDist * factor;
                    NodeMatrix[n22 + NODE_DY] -= yDist * factor;
                  }
                } else {
                  distance = Math.sqrt(xDist * xDist + yDist * yDist);
                  if (distance > 0) {
                    factor = coefficient * NodeMatrix[n1 + NODE_MASS] * NodeMatrix[n22 + NODE_MASS] / distance / distance;
                    NodeMatrix[n1 + NODE_DX] += xDist * factor;
                    NodeMatrix[n1 + NODE_DY] += yDist * factor;
                    NodeMatrix[n22 + NODE_DX] -= xDist * factor;
                    NodeMatrix[n22 + NODE_DY] -= yDist * factor;
                  }
                }
              }
            }
          }
          g2 = options.gravity / options.scalingRatio;
          coefficient = options.scalingRatio;
          for (n3 = 0; n3 < order; n3 += PPN) {
            factor = 0;
            xDist = NodeMatrix[n3 + NODE_X];
            yDist = NodeMatrix[n3 + NODE_Y];
            distance = Math.sqrt(Math.pow(xDist, 2) + Math.pow(yDist, 2));
            if (options.strongGravityMode) {
              if (distance > 0) factor = coefficient * NodeMatrix[n3 + NODE_MASS] * g2;
            } else {
              if (distance > 0)
                factor = coefficient * NodeMatrix[n3 + NODE_MASS] * g2 / distance;
            }
            NodeMatrix[n3 + NODE_DX] -= xDist * factor;
            NodeMatrix[n3 + NODE_DY] -= yDist * factor;
          }
          coefficient = 1 * (options.outboundAttractionDistribution ? outboundAttCompensation : 1);
          for (e2 = 0; e2 < size; e2 += PPE) {
            n1 = EdgeMatrix[e2 + EDGE_SOURCE];
            n22 = EdgeMatrix[e2 + EDGE_TARGET];
            w = EdgeMatrix[e2 + EDGE_WEIGHT];
            ewc = Math.pow(w, options.edgeWeightInfluence);
            xDist = NodeMatrix[n1 + NODE_X] - NodeMatrix[n22 + NODE_X];
            yDist = NodeMatrix[n1 + NODE_Y] - NodeMatrix[n22 + NODE_Y];
            if (adjustSizes === true) {
              distance = Math.sqrt(xDist * xDist + yDist * yDist) - NodeMatrix[n1 + NODE_SIZE] - NodeMatrix[n22 + NODE_SIZE];
              if (options.linLogMode) {
                if (options.outboundAttractionDistribution) {
                  if (distance > 0) {
                    factor = -coefficient * ewc * Math.log(1 + distance) / distance / NodeMatrix[n1 + NODE_MASS];
                  }
                } else {
                  if (distance > 0) {
                    factor = -coefficient * ewc * Math.log(1 + distance) / distance;
                  }
                }
              } else {
                if (options.outboundAttractionDistribution) {
                  if (distance > 0) {
                    factor = -coefficient * ewc / NodeMatrix[n1 + NODE_MASS];
                  }
                } else {
                  if (distance > 0) {
                    factor = -coefficient * ewc;
                  }
                }
              }
            } else {
              distance = Math.sqrt(Math.pow(xDist, 2) + Math.pow(yDist, 2));
              if (options.linLogMode) {
                if (options.outboundAttractionDistribution) {
                  if (distance > 0) {
                    factor = -coefficient * ewc * Math.log(1 + distance) / distance / NodeMatrix[n1 + NODE_MASS];
                  }
                } else {
                  if (distance > 0)
                    factor = -coefficient * ewc * Math.log(1 + distance) / distance;
                }
              } else {
                if (options.outboundAttractionDistribution) {
                  distance = 1;
                  factor = -coefficient * ewc / NodeMatrix[n1 + NODE_MASS];
                } else {
                  distance = 1;
                  factor = -coefficient * ewc;
                }
              }
            }
            if (distance > 0) {
              NodeMatrix[n1 + NODE_DX] += xDist * factor;
              NodeMatrix[n1 + NODE_DY] += yDist * factor;
              NodeMatrix[n22 + NODE_DX] -= xDist * factor;
              NodeMatrix[n22 + NODE_DY] -= yDist * factor;
            }
          }
          var force, swinging, traction, nodespeed, newX, newY;
          if (adjustSizes === true) {
            for (n3 = 0; n3 < order; n3 += PPN) {
              if (NodeMatrix[n3 + NODE_FIXED] !== 1) {
                force = Math.sqrt(
                  Math.pow(NodeMatrix[n3 + NODE_DX], 2) + Math.pow(NodeMatrix[n3 + NODE_DY], 2)
                );
                if (force > MAX_FORCE) {
                  NodeMatrix[n3 + NODE_DX] = NodeMatrix[n3 + NODE_DX] * MAX_FORCE / force;
                  NodeMatrix[n3 + NODE_DY] = NodeMatrix[n3 + NODE_DY] * MAX_FORCE / force;
                }
                swinging = NodeMatrix[n3 + NODE_MASS] * Math.sqrt(
                  (NodeMatrix[n3 + NODE_OLD_DX] - NodeMatrix[n3 + NODE_DX]) * (NodeMatrix[n3 + NODE_OLD_DX] - NodeMatrix[n3 + NODE_DX]) + (NodeMatrix[n3 + NODE_OLD_DY] - NodeMatrix[n3 + NODE_DY]) * (NodeMatrix[n3 + NODE_OLD_DY] - NodeMatrix[n3 + NODE_DY])
                );
                traction = Math.sqrt(
                  (NodeMatrix[n3 + NODE_OLD_DX] + NodeMatrix[n3 + NODE_DX]) * (NodeMatrix[n3 + NODE_OLD_DX] + NodeMatrix[n3 + NODE_DX]) + (NodeMatrix[n3 + NODE_OLD_DY] + NodeMatrix[n3 + NODE_DY]) * (NodeMatrix[n3 + NODE_OLD_DY] + NodeMatrix[n3 + NODE_DY])
                ) / 2;
                nodespeed = 0.1 * Math.log(1 + traction) / (1 + Math.sqrt(swinging));
                newX = NodeMatrix[n3 + NODE_X] + NodeMatrix[n3 + NODE_DX] * (nodespeed / options.slowDown);
                NodeMatrix[n3 + NODE_X] = newX;
                newY = NodeMatrix[n3 + NODE_Y] + NodeMatrix[n3 + NODE_DY] * (nodespeed / options.slowDown);
                NodeMatrix[n3 + NODE_Y] = newY;
              }
            }
          } else {
            for (n3 = 0; n3 < order; n3 += PPN) {
              if (NodeMatrix[n3 + NODE_FIXED] !== 1) {
                swinging = NodeMatrix[n3 + NODE_MASS] * Math.sqrt(
                  (NodeMatrix[n3 + NODE_OLD_DX] - NodeMatrix[n3 + NODE_DX]) * (NodeMatrix[n3 + NODE_OLD_DX] - NodeMatrix[n3 + NODE_DX]) + (NodeMatrix[n3 + NODE_OLD_DY] - NodeMatrix[n3 + NODE_DY]) * (NodeMatrix[n3 + NODE_OLD_DY] - NodeMatrix[n3 + NODE_DY])
                );
                traction = Math.sqrt(
                  (NodeMatrix[n3 + NODE_OLD_DX] + NodeMatrix[n3 + NODE_DX]) * (NodeMatrix[n3 + NODE_OLD_DX] + NodeMatrix[n3 + NODE_DX]) + (NodeMatrix[n3 + NODE_OLD_DY] + NodeMatrix[n3 + NODE_DY]) * (NodeMatrix[n3 + NODE_OLD_DY] + NodeMatrix[n3 + NODE_DY])
                ) / 2;
                nodespeed = NodeMatrix[n3 + NODE_CONVERGENCE] * Math.log(1 + traction) / (1 + Math.sqrt(swinging));
                NodeMatrix[n3 + NODE_CONVERGENCE] = Math.min(
                  1,
                  Math.sqrt(
                    nodespeed * (Math.pow(NodeMatrix[n3 + NODE_DX], 2) + Math.pow(NodeMatrix[n3 + NODE_DY], 2)) / (1 + Math.sqrt(swinging))
                  )
                );
                newX = NodeMatrix[n3 + NODE_X] + NodeMatrix[n3 + NODE_DX] * (nodespeed / options.slowDown);
                NodeMatrix[n3 + NODE_X] = newX;
                newY = NodeMatrix[n3 + NODE_Y] + NodeMatrix[n3 + NODE_DY] * (nodespeed / options.slowDown);
                NodeMatrix[n3 + NODE_Y] = newY;
              }
            }
          }
          return {};
        };
      })();
      var iterate = moduleShim.exports;
      self.addEventListener("message", function(event) {
        var data = event.data;
        NODES = new Float32Array(data.nodes);
        if (data.edges) EDGES = new Float32Array(data.edges);
        iterate(data.settings, NODES, EDGES);
        self.postMessage(
          {
            nodes: NODES.buffer
          },
          [NODES.buffer]
        );
      });
    };
  }
});

// node_modules/graphology-layout-forceatlas2/worker.js
var require_worker = __commonJS({
  "node_modules/graphology-layout-forceatlas2/worker.js"(exports, module) {
    var workerFunction = require_webworker();
    var isGraph = require_is_graph();
    var createEdgeWeightGetter = require_getters().createEdgeWeightGetter;
    var helpers = require_helpers();
    var DEFAULT_SETTINGS = require_defaults();
    function FA2LayoutSupervisor(graph, params) {
      params = params || {};
      if (!isGraph(graph))
        throw new Error(
          "graphology-layout-forceatlas2/worker: the given graph is not a valid graphology instance."
        );
      var getEdgeWeight = createEdgeWeightGetter(
        "getEdgeWeight" in params ? params.getEdgeWeight : "weight"
      ).fromEntry;
      var settings = helpers.assign({}, DEFAULT_SETTINGS, params.settings);
      var validationError = helpers.validateSettings(settings);
      if (validationError)
        throw new Error(
          "graphology-layout-forceatlas2/worker: " + validationError.message
        );
      this.worker = null;
      this.graph = graph;
      this.settings = settings;
      this.getEdgeWeight = getEdgeWeight;
      this.matrices = null;
      this.running = false;
      this.killed = false;
      this.outputReducer = typeof params.outputReducer === "function" ? params.outputReducer : null;
      this.handleMessage = this.handleMessage.bind(this);
      var respawnFrame = void 0;
      var self2 = this;
      this.handleGraphUpdate = function() {
        if (self2.worker) self2.worker.terminate();
        if (respawnFrame) clearTimeout(respawnFrame);
        respawnFrame = setTimeout(function() {
          respawnFrame = void 0;
          self2.spawnWorker();
        }, 0);
      };
      graph.on("nodeAdded", this.handleGraphUpdate);
      graph.on("edgeAdded", this.handleGraphUpdate);
      graph.on("nodeDropped", this.handleGraphUpdate);
      graph.on("edgeDropped", this.handleGraphUpdate);
      this.spawnWorker();
    }
    FA2LayoutSupervisor.prototype.isRunning = function() {
      return this.running;
    };
    FA2LayoutSupervisor.prototype.spawnWorker = function() {
      if (this.worker) this.worker.terminate();
      this.worker = helpers.createWorker(workerFunction);
      this.worker.addEventListener("message", this.handleMessage);
      if (this.running) {
        this.running = false;
        this.start();
      }
    };
    FA2LayoutSupervisor.prototype.handleMessage = function(event) {
      if (!this.running) return;
      var matrix = new Float32Array(event.data.nodes);
      helpers.assignLayoutChanges(this.graph, matrix, this.outputReducer);
      if (this.outputReducer) helpers.readGraphPositions(this.graph, matrix);
      this.matrices.nodes = matrix;
      this.askForIterations();
    };
    FA2LayoutSupervisor.prototype.askForIterations = function(withEdges) {
      var matrices = this.matrices;
      var payload = {
        settings: this.settings,
        nodes: matrices.nodes.buffer
      };
      var buffers = [matrices.nodes.buffer];
      if (withEdges) {
        payload.edges = matrices.edges.buffer;
        buffers.push(matrices.edges.buffer);
      }
      this.worker.postMessage(payload, buffers);
      return this;
    };
    FA2LayoutSupervisor.prototype.start = function() {
      if (this.killed)
        throw new Error(
          "graphology-layout-forceatlas2/worker.start: layout was killed."
        );
      if (this.running) return this;
      this.matrices = helpers.graphToByteArrays(this.graph, this.getEdgeWeight);
      this.running = true;
      this.askForIterations(true);
      return this;
    };
    FA2LayoutSupervisor.prototype.stop = function() {
      this.running = false;
      return this;
    };
    FA2LayoutSupervisor.prototype.kill = function() {
      if (this.killed) return this;
      this.running = false;
      this.killed = true;
      this.matrices = null;
      this.worker.terminate();
      this.graph.removeListener("nodeAdded", this.handleGraphUpdate);
      this.graph.removeListener("edgeAdded", this.handleGraphUpdate);
      this.graph.removeListener("nodeDropped", this.handleGraphUpdate);
      this.graph.removeListener("edgeDropped", this.handleGraphUpdate);
    };
    module.exports = FA2LayoutSupervisor;
  }
});

// node_modules/@react-sigma/layout-core/lib/react-sigma_layout-core.esm.min.js
var r = __toESM(require_react());
var import_react = __toESM(require_react());
function o(r2, n3) {
  const i2 = v(), s3 = (0, import_react.useRef)(n3);
  j(s3.current, n3) || (s3.current = n3);
  return { positions: (0, import_react.useCallback)((() => s3.current ? r2(i2.getGraph(), s3.current) : {}), [i2, s3, r2]), assign: (0, import_react.useCallback)((() => {
    s3.current && r2.assign(i2.getGraph(), s3.current);
  }), [i2, s3, r2]) };
}
function c(r2, n3) {
  const o2 = v(), [c3, u2] = (0, import_react.useState)(false), [p2, g2] = (0, import_react.useState)(null), m2 = (0, import_react.useRef)(n3);
  j(m2.current, n3) || (m2.current = n3), (0, import_react.useEffect)((() => {
    u2(false);
    let t = null;
    return m2.current && (t = new r2(o2.getGraph(), m2.current)), g2(t), () => {
      null !== t && t.kill();
    };
  }), [o2, m2, g2, u2, r2]);
  return { stop: (0, import_react.useCallback)((() => {
    p2 && (p2.stop(), u2(false));
  }), [p2, u2]), start: (0, import_react.useCallback)((() => {
    p2 && (p2.start(), u2(true));
  }), [p2, u2]), kill: (0, import_react.useCallback)((() => {
    p2 && p2.kill(), u2(false);
  }), [p2, u2]), isRunning: c3 };
}
var u;
function p() {
  return p = Object.assign ? Object.assign.bind() : function(t) {
    for (var e2 = 1; e2 < arguments.length; e2++) {
      var r2 = arguments[e2];
      for (var n3 in r2) ({}).hasOwnProperty.call(r2, n3) && (t[n3] = r2[n3]);
    }
    return t;
  }, p.apply(null, arguments);
}
var g;
var m = function(t) {
  return r.createElement("svg", p({ xmlns: "http://www.w3.org/2000/svg", "aria-hidden": "true", className: "play-solid_svg__svg-inline--fa play-solid_svg__fa-play play-solid_svg__fa-w-14", "data-icon": "play", "data-prefix": "fas", viewBox: "0 0 448 512", width: "1em", height: "1em" }, t), u || (u = r.createElement("path", { fill: "currentColor", d: "M424.4 214.7 72.4 6.6C43.8-10.3 0 6.1 0 47.9V464c0 37.5 40.7 60.1 72.4 41.3l352-208c31.4-18.5 31.5-64.1 0-82.6" })));
};
function d() {
  return d = Object.assign ? Object.assign.bind() : function(t) {
    for (var e2 = 1; e2 < arguments.length; e2++) {
      var r2 = arguments[e2];
      for (var n3 in r2) ({}).hasOwnProperty.call(r2, n3) && (t[n3] = r2[n3]);
    }
    return t;
  }, d.apply(null, arguments);
}
var f = function(t) {
  return r.createElement("svg", d({ xmlns: "http://www.w3.org/2000/svg", "aria-hidden": "true", className: "stop-solid_svg__svg-inline--fa stop-solid_svg__fa-stop stop-solid_svg__fa-w-14", "data-icon": "stop", "data-prefix": "fas", viewBox: "0 0 448 512", width: "1em", height: "1em" }, t), g || (g = r.createElement("path", { fill: "currentColor", d: "M400 32H48C21.5 32 0 53.5 0 80v352c0 26.5 21.5 48 48 48h352c26.5 0 48-21.5 48-48V80c0-26.5-21.5-48-48-48" })));
};
function h({ id: e2, className: r2, style: a3, layout: l3, autoRunFor: i2, children: o2, labels: c3 = {} }) {
  const u2 = v(), { stop: p2, start: g2, isRunning: d2 } = l3, h2 = { className: `react-sigma-control ${r2 || ""}`, id: e2, style: a3 };
  return (0, import_react.useEffect)((() => {
    if (!u2) return;
    let t = null;
    return void 0 !== i2 && i2 > -1 && u2.getGraph().order > 0 && (g2(), t = i2 > 0 ? window.setTimeout((() => {
      p2();
    }), i2) : null), () => {
      t && clearTimeout(t);
    };
  }), [i2, g2, p2, u2]), import_react.default.createElement("div", Object.assign({}, h2), import_react.default.createElement("button", { onClick: () => d2 ? p2() : g2(), title: d2 ? c3.stop || "Stop the layout animation" : c3.start || "Start the layout animation" }, o2 && !d2 && o2[0], o2 && d2 && o2[1], !o2 && !d2 && import_react.default.createElement(m, { style: { width: "1em" } }), !o2 && d2 && import_react.default.createElement(f, { style: { width: "1em" } })));
}

// node_modules/@react-sigma/layout-forceatlas2/lib/react-sigma_layout-forceatlas2.esm.min.js
var import_graphology_layout_forceatlas2 = __toESM(require_graphology_layout_forceatlas2());
var import_worker = __toESM(require_worker());
var import_react2 = __toESM(require_react());
function s2(o2 = { iterations: 100 }) {
  return o(import_graphology_layout_forceatlas2.default, o2);
}
function n2(t = {}) {
  return c(import_worker.default, t);
}
var c2 = ({ id: t, className: o2, style: a3, settings: e2 = {}, autoRunFor: s3, children: c3, labels: i2 }) => {
  const u2 = { id: t, className: o2, style: a3, autoRunFor: s3, labels: i2, layout: n2(e2) };
  return import_react2.default.createElement(h, Object.assign({}, u2), c3);
};
export {
  c2 as LayoutForceAtlas2Control,
  s2 as useLayoutForceAtlas2,
  n2 as useWorkerLayoutForceAtlas2
};
//# sourceMappingURL=@react-sigma_layout-forceatlas2.js.map
