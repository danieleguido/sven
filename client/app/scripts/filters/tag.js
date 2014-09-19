'use strict';

/**
 * @ngdoc filter
 * @name svenClientApp.filter:tag
 * @function
 * @description
 * # tag
 * Filter in the svenClientApp.
 */
angular.module('svenClientApp')
  .filter('tag', function () {
    return function (input) {
      return input.split(' - ').shift();
    };
  })
  .filter('percentage', function () {
    return function (input) {
      return (Math.ceil(input*10000)/100) + '%';
    };
  })
  .filter('cmd', function () {
    return function (input) {
      return input.match(/--cmd\s+([a-z]*) -/)[1];
    };
  });
