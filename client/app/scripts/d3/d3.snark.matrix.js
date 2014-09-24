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
          return d.cluster
        };


        

    matrix.init = function(container){
      _svg = container
          .append("svg")
          .attr("height", height)
          .attr("width", width)

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
    matrix.update = function(options){
      if(!_data.length)
        throw "timeline.init does not have data associated";
      // calculate local max and min
      var options = options || {
            measure: 'tf'
          },

          local_min = d3.min(_data, function(d) {return d[options.measure]}),
          local_max = d3.max(_data,function(d) {return d[options.measure]}),
          
          elements = _svg
            .selectAll(".block")
            .data(_data, _key);
      
      
      matrix.draw(elements, {
        min: local_min,
        max: local_max,
        measure: options.measure
      });
    };

    /*
      options.min and options.max
    */
    matrix.draw = function(elements, options) {
      console.log(options);
      
      var size = d3.scale.linear()
        .domain([options.min, options.max])
        .range([2,18]),

        update_selection = elements,
        enter_selection = elements.enter()
          .append("g")
          .attr("class", "block")
        
      // update row elements



      enter_selection
        .append("text")
        .text(function(d) {
          return d.content || '...'
        })
        .attr("y", function(d,i) {
          return i*26 + 26*2;
        })
        .style("fill", "#333333");
      

      update_selection
        .selectAll("circle.global")
        .transition()
          .duration(750)
          .attr("r", function(d){ return size(d[options.measure])})
          .style("fill", function(d){ return d[options.measure]==options.max?"rgb(25,158,154)":"#333333"})
      


      // draw circle (globals)
      enter_selection
        .append("circle")
        .attr("class", "global")
        .style("fill", "#333333")
        .attr("fill-opacity", .3)
        .attr("r", function(d){return size(d[options.measure])})
        .attr("class", "circle")
        .attr("cx", 250)
        .attr("cy", function(d, i) {
          return i*26 + 26*2;
        })


      // for each actor. calculate actor max et actor min
      for(var i=0; i< _data[0].tags.length; i++) {

        console.log('hello', i, _data[0].tags[i])
        update_selection
          .selectAll("circle.tag")
          .transition()
          .duration(750)
          .attr("r", function(d){ return d.tags[i]?
            size(d.tags[i][options.measure]):
            1
          })

        enter_selection
          .append("circle")
          .attr("class", "tag "+_data[0].tags[i].id)
          .style("fill", "#333333")
          .attr("fill-opacity", .4)
          .attr("r", function(d){ return d.tags[i]?
            size(d.tags[i][options.measure]):
            1
          })
          .attr("cx", 280 + (i+1)*60)
          .attr("cy", function(d, i) {
            return i*26 + 26*2;
          })
        //_data[0].tags[i][options.measure]
      }
      

    };

    return matrix;

  }; // end of timeline

  window.snark = snark;
})();