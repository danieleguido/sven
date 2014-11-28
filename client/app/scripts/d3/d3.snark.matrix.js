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
        _headers = [],
        _svg, // the svg container
        
        _key = function(d){
          return d.cluster
        };


    

    matrix.init = function(container){
      _svg = container
          .append("svg")
          .attr("height", height)
          .attr("width", width)
      // appending labels
      _svg
        .append("text")
        .text('concept example')
        .attr({
          x: 40,
          y: 26,
          'class': 'header'
        })

      _svg
        .append("text")
        .text('TF')
        .attr({
          x: 200,
          y: 26,
          'text-anchor': 'middle',
          'class': 'header'
        })

      _svg
        .append("text")
        .text('TFIDF')
        .attr({
          x: 230,
          y: 26,
          'text-anchor': 'middle',
          'class': 'header'
        })
      return matrix;
    };

    matrix.data = function(v, k) {
      if (!arguments.length) return _data;
      _data = v;
      _key = k || _key;
      return matrix;
    };

    matrix.headers = function(v) {
      if (!arguments.length) return _headers;
      _headers = v;
      return matrix;
    };


    matrix.onscroll = function(offset) {
     /* _svg
        .selectAll(".block text")
        .attr('transform', function(d,i) {
          return 'matrix(' + [1, 0, 0, 1, offset.left, 0].join(' ') + ')';
        });
      */
    };

    /*
      enable update enter exit pattern
    */
    matrix.update = function(options){
      if(!_data.length)
        throw "matrix.update error. There aren't any data associated";
      // calculate local max and min
      var options = options || {
            measure: 'tf'
          },

          tf_min = d3.min(_data, function(d) {return d.tf}),
          tf_max = d3.max(_data,function(d) {return d.tf}),

          tfidf_min = d3.min(_data, function(d) {return d.tf_idf}),
          tfidf_max = d3.max(_data,function(d) {return d.tf_idf}),
          
          elements = _svg
            .selectAll('.block')
            .data(_data, _key),

          columns  = _svg
            .selectAll('.column')
            .data(_headers, function(d) {
              return d.id;
            });
      
      // recalculate svg width according to the number of groups
      _svg.attr("width", 260 + _headers.length * 120)

      // cfr http://bost.ocks.org/mike/nest/
      matrix.draw(elements, columns, {
        tf_min: tf_min,
        tf_max: tf_max,
        tfidf_min: tfidf_min,
        tfidf_max: tfidf_max,
        measure: options.measure
      });
    };

    /*
      options.min and options.max
    */
    matrix.draw = function(elements, columns, options) {
      //console.log(options);
      


      var offsetx = 200,

          tf_size = d3.scale.linear()
            .domain([options.tf_min, options.tf_max])
            .range([2,15]),

          tfidf_size = d3.scale.linear()
            .domain([options.tfidf_min, options.tfidf_max])
            .range([2,15]),

        update_selection = elements,
        enter_selection = elements.enter()
          .append('g')
          .attr('class', function(d) {
            return 'block ' + d.status;
          })
          .attr('cid', function(d) {
            return d.id;
          }),
        switchers;
        
        // write text for column headers
        columns.enter()
          .append('text')
          .attr({
            x: function(d,i){ return i*20 + offsetx + 60;},
            y: 40,
            'transform': 'matrix(' + [Math.cos(45), -Math.sin(45), 0, Math.cos(45), Math.sin(45), 1].join(' ') + ')'
          })
          .text(function(d,i){ return d.name})


        // set basic transform for each row (y)
        enter_selection
          .attr('transform', function(d,i) {
            return 'matrix(' + [1, 0, 0, 1, 0, i*26 + 26*2].join(' ') + ')';
          });

        //
        // ADDING ELEMENTS LEFT TO RIGHT
        //
        // append base rectangle
        switchers = enter_selection
          .append('g')
            .attr('class', 'switcher');
        switchers
          .append('circle')
            .attr('class', 'toggler')
            .attr('cid', function(d) {
              return d.id;
            })
            .attr('r', 8)
            .attr('cx', 10)
            .attr('cy', 0)


        // write text labels (they won't change)
        enter_selection
          .append('text')
            .attr({
              x: 40,
              y: 4
            })
            .text(function(d) {
              return d.cluster || '...'
            });

        // adding tfrs
        enter_selection
          .append('circle')
            .attr({
              'class': 'tf',
              cx: offsetx,
              opacity: ".4",
              r: function(d) {
                return tf_size(+d.tf);
              },
              fill: "gold"
            })

        enter_selection
          .append('circle')
            .attr({
              'class': 'tf_idf',
              cx: offsetx + 30,
              opacity: ".4",
              r: function(d) {
                return tfidf_size(+d.tf_idf);
              },
              fill: "gold"
            })


        // write column names


        // adding columns based on headers
        enter_selection
          .selectAll('.measure')
            .data(function(d,i) {
              return _headers.map(function(o) { // put this function outside

                  for(var j=0; j<d.tags.length;j++) {
                    if(d.tags[j].id==o.id) {
                      //o.tf = d.tags[j].tf;
                      //o.tfidf = d.tags[j].tfidf;
                      return {
                        id: d.tags[j].id,
                        tf: d.tags[j].tf,
                        tfidf: d.tags[j].tfidf
                      };
                    }
                  
                };
                // otherwise
                return o;
              });
            }, function(o){
              return o.id
            })
            .enter()
              .append('rect')
              .attr({
                'class'    : 'measure',
                'width'    : 60,
                'height'   : 1,
                'y'        : -0.5,
                'gid'  : function(d) {return d.id},
                'x'        : function(d,i) {return i*60 + offsetx + 60;}
              });


        update_selection
          .transition(500)
          .attr('transform', function(d,i) {
            return 'matrix(' + [1, 0, 0, 1, 0, i*26 + 26*2].join(' ') + ')';
          })
          .attr('class', function(d) {
              return 'block ' + d.status;
            })
          .selectAll('.measure')
            .attr('height', function(d){
                if(options.measure == 'tf')
                  return tf_size(+d.tf||0)*2;
                else
                  return tfidf_size(+d.tf_idf||0)*2;
              })
            .attr('y', function(d){
                if(options.measure == 'tf')
                  return -tf_size(+d.tf||0);
                else
                  return -tfidf_size(+d.tf_idf||0);
              })
              

        update_selection
          .exit()
          .remove()
          
        return matrix;
      };

    return matrix;

  }; // end of timeline

  window.snark = snark;
})();