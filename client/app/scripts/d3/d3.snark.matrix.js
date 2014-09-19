(function($, undefined){
  'use strict';

  var snark = window.snark || {};

  /*
    A 2d matrix chart to handle moulti column crossings.
    A reusable chart which is it not reusable, though.
    Handle with care.
    Usage type
    
    if(!timeline) {
      timeline = snark.timeline()
        .init(d3.select("#timeline"));
    };

    timeline
      .key(function(d){ console.log(d); return +d.key})
      .xValue(function(d){ console.log(d); return +d.key})
      .yValue(function(d){ console.log(d); return (+d.value)})
      .data(years)
      .update();
  */
  snark.matrix = function(){
    var matrix = {},
        width = 1000,
        height = 1352,
        margin = {top: 12, right: 12, bottom: 12, left: 12},

        _data = [],
        _svg, // the svg container
        
        _key = function(d){
          console.log(d.cluster);
          return d.cluster
        };


        

    matrix.init = function(container){
      _svg = container
          .append("svg")
          .attr("height", height)

      _svg
        .append("text")
        .text('GTF')
        .attr("x", 250)
        .attr("y", 26)

      return matrix;
    };

    matrix.data = function(v, k) {
      if (!arguments.length) return _data;
      _data = v;
      _key = k || _key;
      return matrix;
    };

    /*
      enable update enter exit pattern
    */
    matrix.update = function(){
      if(!_data.length)
        throw "timeline.init does not have data associated";
      // calculate local max and min

      var elements = _svg
            .selectAll(".block")
            .data(_data, _key);

      matrix.draw(elements);
    };

    matrix.draw = function(elements) {
      var enter_selection = elements.enter()
        .append("g")
        .attr("class", "block");

      

      enter_selection
        enter_selection
        .append("text")
        .text(function(d) {
          return d.content || '...'
        })
        .attr("y", function(d,i) {
          console.log(d,i);
          return i*26 + 26*2;
        })
        .style("fill", "#333333");

      // draw circle (globals)
      enter_selection
        .append("circle")
        .style("fill", "#333333")
        .attr("fill-opacity", .2)
        .attr("r", 10)
        .attr("class", "circle")
        .attr("cx", 250)
        .attr("cy", function(d, i) {
          return i*26 + 26*2;
        })
    };

    return matrix;

  }; // end of timeline

  window.snark = snark;
})();