import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

// Set html height to 100% to make the svg height 100% of the parent div
document.documentElement.style.height = "100%";

// Specify the charts’ dimensions. The height is variable, depending on the layout.
const width = 1200;
const height = 600;
const marginTop = 10;
const marginRight = 10;
const marginBottom = 10;
const marginLeft = 40;

// Rows are separated by dx pixels, columns by dy pixels. These names can be counter-intuitive
// (dx is a height, and dy a width). This because the tree must be viewed with the root at the
// “bottom”, in the data domain. The width of a column is based on the tree’s height.

const data = JSON.parse(scenario.value);
console.log("data", data);
const root = d3.hierarchy(data);
const dx = 70;
const dy = (width - marginRight - marginLeft) / (1 + root.height);

// Define the tree layout and the shape for links.
const tree = d3.tree().nodeSize([dx, dy]);
const diagonal = d3
  .linkHorizontal()
  .x((d) => d.y)
  .y((d) => d.x);

const container = d3
  .select("#grafico") // Assuming 'grafico' is the id of the parent div
  .style("display", "flex")
  .style("justify-content", "center");
// .style("align-items", "center")
// .style("height", "100vh"); // Set the height to the full viewport height

const svg = container
  .append("svg")
  .attr("width", width)
  .attr("height", height)
  .attr("viewBox", [-marginLeft, -marginTop, width, height])
  .attr(
    "style",
    "width: auto; height: auto; font: 16px sans-serif; user-select: none;"
  );

// Create the SVG container, a layer for the links and a layer for the nodes.
//const svg = d3
//  .create("svg")
//  .attr("width", width)
//  .attr("height", height) // Set the height
//  .attr("viewBox", [-marginLeft, -marginTop, width, height]) // Adjust the viewBox to match the new height
//  //.attr("height", dx)
//  //.attr("viewBox", [-marginLeft, -marginTop, width, dx])
//  .attr(
//    "style",
//    "width: auto; height: auto; font: 16px sans-serif; user-select: none;"
//  );

const gLink = svg
  .append("g")
  .attr("fill", "none")
  .attr("stroke", "#555")
  .attr("stroke-opacity", 0.4)
  .attr("stroke-width", 1.5);

const gNode = svg
  .append("g")
  .attr("cursor", "pointer")
  .attr("pointer-events", "all");

function update(event, source) {
  const duration = event?.altKey ? 2500 : 250; // hold the alt key to slow down the transition
  const nodes = root.descendants().reverse();
  const links = root.links();

  // Compute the new tree layout.
  tree(root);

  let left = root;
  let right = root;
  root.eachBefore((node) => {
    if (node.x < left.x) left = node;
    if (node.x > right.x) right = node;
  });

  //const height = right.x - left.x + marginTop + marginBottom;

  const transition = svg
    .transition()
    .duration(duration)
    .attr("height", height)
    .attr("viewBox", [-marginLeft, left.x - marginTop, width, height])
    .tween(
      "resize",
      window.ResizeObserver ? null : () => () => svg.dispatch("toggle")
    );

  // Update the nodes…
  const node = gNode.selectAll("g").data(nodes, (d) => d.id);

  // Enter any new nodes at the parent's previous position.
  const nodeEnter = node
    .enter()
    .append("g")
    .attr("transform", (d) => `translate(${source.y0},${source.x0})`)
    .attr("fill-opacity", 0)
    .attr("stroke-opacity", 0)
    .attr("id", (d) => `node-${d.id}`)
    .on("click", (event, d) => {
      d.children = d.children ? null : d._children;
      update(event, d);
    });

  nodeEnter.each(function (d) {
    // Check if the node is a middle node
    if (d.parent && d._children) {
      d3.select(this)
        .append("foreignObject")
        .attr("width", 55)
        .attr("height", 50)
        .attr("x", -55)
        .attr("y", 10)
        .append("xhtml:body")
        .html(
          `<button style="background-color: red; color: white; border: none; text-align: center; font-size: 16px; cursor: pointer; border-radius: 10px;" id="prune-${d.id}">Podar</button>`
        )
        .on("click", function (event) {
          event.stopPropagation(); // Prevent click event from propagating to outer elements

          // Get the data bound to the parent g element
          const nodeData = d3.select(this.parentNode).datum();

          // Toggle the pruned state
          const newState = !nodeData.data.pruned;

          // If the new state is false but the parent is pruned, ignore
          if (!newState && nodeData.parent.data.pruned) return;

          // Mark the node as pruned or not pruned
          nodeData.data.pruned = newState;

          // Mark all children as pruned or not pruned
          const markDescendants = (node) => {
            node.data.pruned = newState;
            if (node._children)
              node._children.forEach((child) => markDescendants(child));
          };
          markDescendants(nodeData);

          // Mark all descendants as pruned or not pruned
          // nodeData.each((d) => (d.data.pruned = newState));

          // Update the tree
          update(event, nodeData);
        });
    }
  });

  nodeEnter.append("circle").attr("r", 2.5).attr("stroke-width", 10);

  nodeEnter
    .append("text")
    .attr("dy", "0.31em")
    .attr("x", (d) => {
      if (!d.parent) return -3;
      else return 5;
      // return d._children ? -6 : 6;
    })
    .attr("y", (d) => {
      if (!d.parent) return 15;
      else return 15;
      // return d._children ? -6 : 6;
    })
    // .attr("text-anchor", (d) => (!d.parent ? "end" : "start"))
    .attr("text-anchor", "start")
    .text((d) => d.data.name)
    .clone(true)
    .lower()
    .attr("stroke-linejoin", "round")
    .attr("stroke-width", 3)
    .attr("stroke", "white");

  // Transition nodes to their new position.
  const nodeUpdate = node
    .merge(nodeEnter)
    .transition(transition)
    .attr("transform", (d) => `translate(${d.y},${d.x})`)
    .attr("fill-opacity", 1)
    .attr("stroke-opacity", 1);

  nodeUpdate
    .select("circle")
    .attr("fill", (d) =>
      d.data.pruned ? "red" : d._children ? "#555" : "#999"
    );

  nodeUpdate
    .selectAll("text")
    .style("fill", (d) => (d.data.pruned ? "red" : "black"));

  // Update the prune buttons
  nodeUpdate.each(function (d) {
    // Check if the node is a middle node
    if (d.parent && d._children) {
      d3.select(this)
        .select("foreignObject")
        .select("button")
        .style("background-color", d.data.pruned ? "grey" : "red");
    }
  });

  // Transition exiting nodes to the parent's new position.
  const nodeExit = node
    .exit()
    .transition(transition)
    .remove()
    .attr("transform", (d) => `translate(${source.y},${source.x})`)
    .attr("fill-opacity", 0)
    .attr("stroke-opacity", 0);

  // Update the links…
  const link = gLink.selectAll("path").data(links, (d) => d.target.id);

  // Enter any new links at the parent's previous position.
  const linkEnter = link
    .enter()
    .append("path")
    // .attr("id", (d) => `link-${d.source.data.id}-${d.target.data.id}`)
    .attr("d", (d) => {
      const o = { x: source.x0, y: source.y0 };
      return diagonal({ source: o, target: o });
    })
    .attr("stroke", (d) => (d.target.data.pruned ? "red" : "#555"));

  // Transition links to their new position.
  link
    .merge(linkEnter)
    .transition(transition)
    .attr("d", diagonal)
    .attr("stroke", (d) => (d.target.data.pruned ? "red" : "#555"));

  // Transition exiting nodes to the parent's new position.
  link
    .exit()
    .transition(transition)
    .remove()
    .attr("d", (d) => {
      const o = { x: source.x, y: source.y };
      return diagonal({ source: o, target: o });
    });

  // Stash the old positions for transition.
  root.eachBefore((d) => {
    d.x0 = d.x;
    d.y0 = d.y;
  });
}

// Do the first update to the initial configuration of the tree — where a number of nodes
// are open (arbitrarily selected as the root, plus nodes with 7 letters).
root.x0 = dy / 2;
root.y0 = 0;
root.descendants().forEach((d, i) => {
  d.id = i;
  d._children = d.children;
  // if (d.depth && d.data.name.length !== 7) d.children = null;
});

update(null, root);

grafico.appendChild(svg.node());

function pruneTree(node) {
  if (node.data.pruned) return null;
  const newNode = { ...node.data };
  if (node.children)
    newNode.children = node.children.map(pruneTree).filter(Boolean);
  return newNode;
}

window.exportar = function () {
  const prunedRoot = pruneTree(root);
  const data = JSON.stringify(prunedRoot, null, 2);
  const blob = new Blob([data], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "arbol.json";
  a.click();
  URL.revokeObjectURL(url);
};
